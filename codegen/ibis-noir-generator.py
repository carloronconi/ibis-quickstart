import subprocess

import inspect

import ibis

from ibis.common.graph import Graph, Node
import ibis.expr.operations as ops
import ibis.expr.types as typ
from ibis.expr.visualize import to_graph
from typing import List, Sequence, Tuple
import operators as sop


def q_inner_join(tables: list[typ.relations.Table]) -> typ.relations.Table:
    return (tables[0]
            .join(tables[1], "int1"))


def q_outer_join(tables: list[typ.relations.Table]) -> typ.relations.Table:
    return (tables[0]
            .outer_join(tables[1], "int1"))


def q_left_join(tables: list[typ.relations.Table]) -> typ.relations.Table:
    return (tables[0]
            .left_join(tables[1], "int1"))


def q_filter_group_mutate_reduce(tables: list[typ.relations.Table]) -> typ.relations.Table:
    table = tables[0]
    return (table
            .filter(table.string1 == "unduetre")
            .group_by("string1").aggregate()
            .mutate(int1=table.int1 * 20)
            .aggregate(by=["string1"], max=table.int1.max()))


def q_filter_group_mutate(tables: list[typ.relations.Table]) -> typ.relations.Table:
    table = tables[0]
    return (table
            .filter(table.string1 == "unduetre")
            .group_by("string1").aggregate()
            .mutate(int1=table.int1 * 20))  # mutate always results in alias preceded by Multiply (or other bin op)


def q_filter_select(tables: list[typ.relations.Table]) -> typ.relations.Table:
    table = tables[0]
    return (table
            .filter(table.string1 == "unduetre")
            .select("int1"))


def q_filter_filter_select(tables: list[typ.relations.Table]) -> typ.relations.Table:
    table = tables[0]
    return (table
            .filter(table.int1 == 123)
            .filter(table.string1 == "unduetre")
            # .select("int1", "string1")    # double select is unsupported: select does Cols -> tuple so no way for
            .select("string1"))             # second select to decide number to go in .map(|x| x.num) based on col name


def q_filter_group_select(tables: list[typ.relations.Table]) -> typ.relations.Table:
    table = tables[0]
    return (table
            .filter(table.string1 == "unduetre")
            .group_by("string1").aggregate()
            .select("string1"))


def run_noir_query_on_table(table_files: list[str], query_gen):
    tables = []
    tups = []
    for table_file in table_files:
        tab = ibis.read_csv(table_file)
        tables.append(tab)
        tups.append((table_file, tab))

    query = query_gen(tables)

    operators = create_operators(query, tables[0])
    reorder_operators(operators, query_gen)

    gen_noir_code(operators, tups)

    subprocess.run("cd noir-template && cargo-fmt && cargo run", shell=True)


def create_operators(query: ibis.expr.types.relations.Table, table: typ.relations.Table) -> List[sop.Operator]:
    print("parsing query...")

    to_graph(query).render("out/query3")
    subprocess.run("open out/query3.pdf", shell=True)

    graph = Graph.from_bfs(query.op(), filter=ops.Node)  # filtering ops.Selection doesn't work

    operators: list[sop.Operator] = []
    for tup in graph.items():
        operator = tup[0]
        operands = tup[1]
        print(str(operator) + " |\t" + type(operator).__name__ + ":\t" + str(operands))

        match operator:
            case ops.relations.Join():
                operators.append(sop.JoinOperator(table, operator))

            case ops.core.Alias() if one_reduction_operand(operands):  # find reducers (aka reduce)
                operand = operands[0]
                operators.append(sop.ReduceOperator(operand))

            case ops.core.Alias() if one_numeric_operand(operands):  # find mappers (aka map)
                operand = operands[0]  # maps have a single operand
                operators.append(sop.MapOperator(table, operand, operators))

            case ops.relations.Aggregation():  # find groupers (aka group by)
                operators.append(sop.GroupOperator(table, operator.by))  # by contains list of all group by columns

            case ops.logical.Comparison():  # find filters (aka row selection)
                operators.append(sop.FilterOperator(table, operator))

            case ops.relations.Selection():  # find maps (aka column projection)
                selected_columns = []
                for operand in filter(lambda o: isinstance(o, ops.TableColumn), operands):
                    selected_columns.append(operand)
                if selected_columns:
                    operators.append(sop.SelectOperator(table, selected_columns, operators))

    print("done parsing")
    # all nodes have a 'name' attribute and a 'dtype' and 'shape' attributes: use those to get info!

    return operators


def reorder_operators(operators: List[sop.Operator], query_gen):
    operators.reverse()

    source = inspect.getsource(query_gen).splitlines()
    source = list(filter(lambda l: l.startswith("."), map(lambda l: l.strip(), source)))

    # swap-sort the operators according to the parsed ibis query
    for i, line in enumerate(source):
        line_op = line.strip().split(".")[1].split("(")[0]
        if not line_op == operators[i].ibis_api_name():
            for j in range(i + 1, len(operators)):
                if line_op == operators[j].ibis_api_name():
                    operators[i], operators[j] = operators[j], operators[i]
                    break

    # filter out additional operators
    while len(operators) > len(source):
        operators.pop()


def gen_noir_code(operators: List[sop.Operator], tables: List[Tuple[str, typ.relations.Table]]):
    print("generating noir code...")

    with open("noir-template/main_top.rs") as f:
        top = f.read()
    top = gen_noir_code_top(top, tables)

    with open("noir-template/main_bot.rs") as f:
        bot = f.read()

    mid = ""
    for op in operators:
        mid = op.generate(mid)

    with open('noir-template/src/main.rs', 'w') as f:
        f.write(top)
        f.write(mid)
        f.write(bot)

    print("Done generating code")


def gen_noir_code_top(top: str, tables: List[Tuple[str, typ.relations.Table]]):
    body = top + ""
    names = []
    for file, table in tables:
        # define struct for table's columns
        name = table.get_name()
        columns = table.columns
        body += f"#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq)]\nstruct Cols_{name} {{"
        for i, col in enumerate(columns):
            body += f"{col}: {to_noir_type(table, i)},"
        body += "}\n"

    body += "\nfn logic(ctx: &StreamContext) {\n"

    for file, table in tables:
        # define table
        name = table.get_name()
        names.append(name)
        body += f"let {name} = ctx.stream_csv::<Cols_{name}>(\".{file}\");\n"

    body += names.pop(0)
    return body


def to_noir_type(table: typ.relations.Table, index: int) -> str:
    ibis_to_noir_type = {"Int64": "i64", "String": "String"}  # TODO: add nullability with optionals
    ibis_type = table.schema().types[index]
    return ibis_to_noir_type[ibis_type.name]


def one_numeric_operand(operands: Sequence[Node]) -> bool:
    if len(operands) != 1:
        return False
    if getattr(operands[0], '__module__', None) != ibis.expr.operations.numeric.__name__:
        return False
    return True


def one_reduction_operand(operands: Sequence[Node]) -> bool:
    if len(operands) != 1:
        return False
    return isinstance(operands[0], ibis.expr.operations.Reduction)


if __name__ == '__main__':
    table_files = ["./data/int-1-string-1.csv", "./data/int-3.csv"]

    # query_gen = q_filter_select
    # query_gen = q_filter_filter_select
    # query_gen = q_filter_group_select
    # query_gen = q_filter_group_mutate
    # query_gen = q_filter_group_mutate_reduce
    # query_gen = q_inner_join
    # query_gen = q_outer_join
    query_gen = q_left_join

    run_noir_query_on_table(table_files, query_gen)