import os
import unittest

import ibis
import pandas as pd

from codegen import compile_ibis_to_noir
from codegen import ROOT_DIR
from ibis import _
from difflib import unified_diff


class TestOperators(unittest.TestCase):

    def test_filter_select(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.string1 == "unduetre")
                 .select("int1"))

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-select.rs")

    def test_filter_filter_select_select(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.int1 == 123)
                 .filter(table.string1 == "unduetre")
                 .select("int1", "string1")
                 .select("string1"))

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-filter-select-select.rs")

    def test_filter_group_select(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.string1 == "unduetre")
                 .group_by("string1")
                 .aggregate(int1_agg=table["int1"].first())
                 .select(["int1_agg"]))

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-group-select.rs")

    def test_filter_group_mutate(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.string1 == "unduetre")
                 .group_by("string1")
                 .aggregate(int1_agg=table["int1"].first())
                 .mutate(mul=_.int1_agg * 20))  # mutate always results in alias preceded by Multiply (or other bin op)

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-group-mutate.rs")

    def test_filter_reduce(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.string1 == "unduetre")
                 .aggregate(int1_agg=table["int1"].sum()))
        # here example of reduce without group_by

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-reduce.rs")

    def test_filter_group_mutate_reduce(self):
        file = ROOT_DIR + "/data/int-1-string-1.csv"
        table = ibis.read_csv(file)
        query = (table
                 .filter(table.int1 > 200)
                 .mutate(mul=_.int1 * 20)
                 .group_by("string1")
                 # it makes no sense to mutate after group_by: as if didn't group_by! mutate before it
                 .aggregate(agg=_.mul.sum()))

        # Solution (works because of two blocks below):
        # 1. encounter aggregate
        # 2. if has TableColumn below it's a group_by().reduce()
        # 3. otherwise it's just a reduce()

        # Not performing aggregation right after group by will ignore the group by!
        # .group_by("string1")
        # .mutate(mul=_.int1 * 20)
        # .aggregate(agg=_.mul.sum()))

        # Only ibis use case with group by not followed by aggregate
        # Still, it performs an almost-aggregation right after
        # For now not supporting this type of operator (can be expressed with
        # normal group by + reduce)
        # .group_by("string1")
        # .aggregate(int1_agg=table["int1"].first())
        # .mutate(center=_.int1 - _.int1.mean()))

        self.cleanup()
        compile_ibis_to_noir([(file, table)], query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/filter-group-mutate-reduce.rs")

    def test_inner_join_select(self):
        files = [ROOT_DIR + "/data/int-1-string-1.csv", ROOT_DIR + "/data/int-3.csv"]
        tables = [ibis.read_csv(file) for file in files]
        query = (tables[0]
                 .filter(_.int1 < 200)
                 .mutate(mul=_.int1 * 20)
                 .join(tables[1]
                       .mutate(sum=_.int3 + 100), "int1")
                 .select(["string1", "int1", "int3"])
                 )

        self.cleanup()
        compile_ibis_to_noir(zip(files, tables), query, run_after_gen=True, render_query_graph=False)
        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/inner-join-select.rs")

    def test_outer_join(self):
        files = [ROOT_DIR + "/data/int-1-string-1.csv", ROOT_DIR + "/data/int-3.csv"]
        tables = [ibis.read_csv(file) for file in files]
        query = (tables[0]
                 .outer_join(tables[1], "int1"))

        self.cleanup()
        compile_ibis_to_noir(zip(files, tables), query, run_after_gen=False, render_query_graph=False)

        print(query.head(20).to_pandas())

        # TODO: printing to file with Serde fails because some values are NaN: don't test output for now (same for left join)
        # self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/outer-join.rs")

    def test_left_join(self):
        files = [ROOT_DIR + "/data/int-1-string-1.csv", ROOT_DIR + "/data/int-3.csv"]
        tables = [ibis.read_csv(file) for file in files]
        query = (tables[0]
                 .left_join(tables[1], "int1"))

        self.cleanup()
        compile_ibis_to_noir(zip(files, tables), query, run_after_gen=False, render_query_graph=False)

        print(query.head(20).to_pandas())

        # self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/left-join.rs")

    def test_group_reduce_join_mutate(self):
        """
        Tests two cases:
        - mutate (could also be select) after join (which produces a KeyedStream of a tuple of joined structs)
        - group-reduce KeyedStream join with Stream (KeyedStream wants to join with another KeyedStream)
        """
        files = [ROOT_DIR + "/data/int-1-string-1.csv", ROOT_DIR + "/data/int-3.csv"]
        tables = [ibis.read_csv(file) for file in files]
        query = (tables[1]
                 .group_by("int1")
                 .aggregate(agg2=_.int2.sum())
                 .inner_join(tables[0], "int1")
                 .mutate(mut4=_.int4 + 100))

        self.cleanup()
        compile_ibis_to_noir(zip(files, tables), query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/group-reduce-join-mutate.rs")

    def test_group_reduce_group_reduce_join(self):
        """
        Tests joining KeyedStream with other var which is KeyedStream already
        """

        files = [ROOT_DIR + "/data/int-1-string-1.csv", ROOT_DIR + "/data/int-3.csv"]
        tables = [ibis.read_csv(file) for file in files]
        query = (tables[1]
                 .group_by("int1")
                 .aggregate(agg2=_.int2.sum())
                 .inner_join(tables[0]
                             .group_by("int1").aggregate(agg4=_.int4.sum()), "int1"))

        self.cleanup()
        compile_ibis_to_noir(zip(files, tables), query, run_after_gen=True, render_query_graph=False)

        print(query.head(20).to_pandas())

        self.assert_similarity_noir_output(query)
        self.assert_equality_noir_source("/test/expected/group-reduce-group-reduce-join.rs")

    def cleanup(self):
        try:
            os.remove(ROOT_DIR + "/out/noir-result.csv")
        except FileNotFoundError:
            pass

    def assert_equality_noir_source(self, test_expected_file: str):
        with open(ROOT_DIR + test_expected_file, "r") as f:
            expected_lines = f.readlines()
        with open(ROOT_DIR + "/noir-template/src/main.rs", "r") as f:
            actual_lines = f.readlines()

        diff = list(unified_diff(expected_lines, actual_lines))
        self.assertEqual(diff, [], "Differences:\n" + "".join(diff))
        print("\033[92m Source equality: OK\033[00m")

    def assert_similarity_noir_output(self, query):
        df_ibis = query.to_pandas()

        df_noir = pd.read_csv(ROOT_DIR + "/out/noir-result.csv", header=None)

        equal_cols = 0
        equal_col_names = []
        for col_ibis_name in df_ibis.columns:
            for col_noir_name in df_noir.columns:
                col_ibis = sorted(df_ibis[col_ibis_name].to_list())
                col_noir = sorted(df_noir[col_noir_name].to_list())
                if col_noir == col_ibis:
                    equal_col_names.append(col_noir_name)
                    df_noir.drop(col_noir_name, axis=1, inplace=True)
                    equal_cols += 1
                    break

        # check if all ibis columns are present in noir columns (with elements in any order)
        self.assertTrue(equal_cols == len(df_ibis.columns))

        df_noir = pd.read_csv(ROOT_DIR + "/out/noir-result.csv", header=None)
        for col in df_noir.columns:
            if col not in equal_col_names:
                df_noir.drop(col, axis=1, inplace=True)

        for i, row_ibis in df_ibis.iterrows():
            row_ibis = set(row_ibis.to_list())
            for n, row_noir in df_noir.iterrows():
                row_noir = set(row_noir.to_list())
                if row_noir == row_ibis:
                    df_noir.drop(n, axis="index", inplace=True)
                    break

        # check if each ibis row contain same set of values as one noir row (set due to strings not being sortable with ints)
        self.assertTrue(len(df_noir.index) == 0)
        print(f"\033[92m Output similarity: OK\033[00m")


if __name__ == '__main__':
    unittest.main()
