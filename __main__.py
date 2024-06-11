import argparse
import ibis
from pyflink.table import EnvironmentSettings, TableEnvironment


def main():
    # Example standalone usage:
    # python ../ibis-renoir-compiler test.test_operators.TestNullableOperators.test_nullable_filter_filter_select_select --paths /home/carlo/Projects/ibis-renoir-compiler/data/int-1-string-1.csv /home/carlo/Projects/ibis-renoir-compiler/data/int-3.csv
    # Example hyperfine usage:
    # hyperfine --warmup 5 "python ../ibis-renoir-compiler test.test_operators.TestNullableOperators.test_nullable_filter_filter_select_select --paths /home/carlo/Projects/ibis-renoir-compiler/data/int-1-string-1.csv /home/carlo/Projects/ibis-renoir-compiler/data/int-3.csv" --export-json result.json
    # Example hyperfine usage comparing renoir and polars:
    # hyperfine --warmup 5 "python ../ibis-renoir-compiler test.test_operators.TestNullableOperators.test_nullable_filter_filter_select_select --paths /home/carlo/Projects/ibis-renoir-compiler/data/int-1-string-1.csv /home/carlo/Projects/ibis-renoir-compiler/data/int-3.csv --backend renoir" "python ../ibis-renoir-compiler test.test_operators.TestNullableOperators.test_nullable_filter_filter_select_select --paths /home/carlo/Projects/ibis-renoir-compiler/data/int-1-string-1.csv /home/carlo/Projects/ibis-renoir-compiler/data/int-3.csv --backend polars" --export-json result.json
    parser = argparse.ArgumentParser("ibis-renoir-compiler")
    parser.add_argument(
        "test_case", help="Which testcase to run. Use `python -m benchmark.discover_tests` to see the current list of tests.", type=str)
    parser.add_argument(
        "--path_suffix", help="Suffix for test files used by test_case. Useful for having same file with growing sizes.", default="", type=str)
    parser.add_argument("--backend", help="Which backend to use.", type=str, choices=[
                        "renoir", "duckdb", "snowflake", "flink", "polars"], default="renoir")
    args = parser.parse_args()

    test_class, test_case = args.test_case.rsplit(".", 1)

    # because we're not using unittest's harness, we need to set the method name manually
    test_instance = eval(f"{test_class}(\"{test_case}\")")
    test_instance.init_table_files(file_suffix=args.path_suffix)
    test_instance.run_after_gen = True
    test_instance.render_query_graph = False
    # leaving logging on doesn't seem to affect performance
    # test_instance.benchmark = None
    test_instance.perform_assertions = False
    test_instance.perform_compilation = True if args.backend == "renoir" else False
    # when running performance benchmarks, don't write to file
    test_instance.print_output_to_file = False

    eval(f"test_instance.{test_case}()", {"test_instance": test_instance})
    # If the backend is renoir, we have already performed the compilation to renoir code and ran it
    if (args.backend == "renoir"):
        if (test_instance.benchmark is not None):
            test_instance.benchmark.log()
        return

    # Else, the test we ran simply populated the query attribute with the ibis query
    # and we can run it using to_pandas(), after setting the backend to the desired one
    # Flink requires special setup
    if (args.backend == "flink"):
        table_env = TableEnvironment.create(
            EnvironmentSettings.in_streaming_mode())
        con = ibis.flink.connect(table_env)
        ibis.set_backend(con)
    else:
        ibis.set_backend(args.backend)
    test_instance.query.to_pandas().head()
    print(f"finished running query with: {ibis.get_backend().name}")


if __name__ == "__main__":
    main()
