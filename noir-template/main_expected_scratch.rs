use std::fs::File;
use std::io;
use std::io::Write;
use noir_compute::prelude::*;
use serde::{Deserialize, Serialize};
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq)]
struct Struct_var_0 {
    int1: i64,
    int2: i64,
    int3: i64,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Hash)]
struct Struct_var_1 {
    int1: i64,
    int2: i64,
    int3: i64,
    sum: i64,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq)]
struct Struct_var_2 {
    int1: i64,
    string1: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Hash)]
struct Struct_var_3 {
    int1: i64,
    string1: String,
    mul: i64,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq)]
struct Struct_var_4 {
    int1: i64,
    string1: String,
    mul: i64,
    int2: i64,
    int3: i64,
    sum: i64,
}

fn logic(ctx: StreamContext) {
    let var_0 =
        ctx.stream_csv::<Struct_var_0>("/home/carlo/Projects/ibis-quickstart/data/int-3.csv");
    let var_1 = var_0.map(|x| Struct_var_1 {
        int1: x.int1,
        int2: x.int2,
        int3: x.int3,
        sum: x.int3 + 100,
    });
    let var_2 = ctx
        .stream_csv::<Struct_var_2>("/home/carlo/Projects/ibis-quickstart/data/int-1-string-1.csv");
    let var_4 = var_2
        .filter(|x| x.int1 < 200)
        .map(|x| Struct_var_3 {
            int1: x.int1,
            string1: x.string1,
            mul: x.int1 * 20,
        })
        .join(var_1, |x| x.int1, |y| y.int1)
        //.map(|(join_col, join_tup)| join_tup.0)
        //.drop_key()
        //.unique_assoc()
        ;

    let out = var_4.collect_vec();

    tracing::info!("starting execution");
    ctx.execute_blocking();

    let out = out.get().unwrap();

    let mut wtr = csv::WriterBuilder::new()
        .has_headers(false)
        .from_writer(io::stdout());

    for e in out {
        wtr.serialize(e).unwrap();
    }
    wtr.flush().unwrap();

    // TODO: two extra "123" rows (one from join col being retained as key) compared to ibis

    //let lines: Vec<String> = out.iter()
    //    .map(|e| format!("{:?}", e))
    //    .collect();
    //let mut file = File::create("./result").unwrap();
    //writeln!(file, "{}", lines.join("\n")).unwrap();

}

fn main() -> eyre::Result<()> {
    color_eyre::install().ok();
    tracing_subscriber::fmt::init();

    let ctx = StreamContext::default();

    tracing::info!("building graph");
    logic(ctx);

    tracing::info!("finished execution");

    Ok(())
}
