use renoir::prelude::*;
use serde::{Deserialize, Serialize};
use std::cmp::max;
use std::fs::File;
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_0 {
    int1: Option<i64>,
    string1: Option<String>,
    int4: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_1 {
    int1: Option<i64>,
    agg4: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_2 {
    int1: Option<i64>,
    int2: Option<i64>,
    int3: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_3 {
    int1: Option<i64>,
    int2: Option<i64>,
    int3: Option<i64>,
    int1_right: Option<i64>,
    agg4: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_collect {
    int1: Option<i64>,
}

fn logic(ctx: StreamContext) {
    let var_0 = ctx
        .stream_csv::<Struct_var_0>("/home/carlo/Projects/ibis-quickstart/data/int-1-string-1.csv");
    let var_1 = var_0
        .group_by(|x| (x.int1.clone()))
        .reduce(|a, b| {
            a.int4 = a.int4.zip(b.int4).map(|(x, y)| x + y);
        })
        .map(|(k, x)| Struct_var_1 {
            int1: k.clone(),
            agg4: x.int4,
        });
    let var_2 =
        ctx.stream_csv::<Struct_var_2>("/home/carlo/Projects/ibis-quickstart/data/int-3.csv");
    let var_3 = var_2
        .group_by(|x| x.int1.clone())
        .join(var_1)
        .map(|(_, x)| Struct_var_3 {
            int1: x.0.int1,
            int2: x.0.int2,
            int3: x.0.int3,
            int1_right: x.1.int1,
            agg4: x.1.agg4,
        });
    let out = var_3.collect_vec();
    tracing::info!("starting execution");
    ctx.execute_blocking();
    let out = out.get().unwrap();
    let out = out
        .iter()
        .map(|(k, v)| (Struct_collect { int1: k.clone() }, v))
        .collect::<Vec<_>>();
    let file = File::create("../out/noir-result.csv").unwrap();
    let mut wtr = csv::WriterBuilder::new().from_writer(file);

    for e in out {
        wtr.serialize(e).unwrap();
    }
    wtr.flush().unwrap();
}

fn main() -> eyre::Result<()> {
    color_eyre::install().ok();
    tracing_subscriber::fmt::init();

    let ctx = StreamContext::new_local();

    tracing::info!("building graph");
    logic(ctx);

    tracing::info!("finished execution");

    Ok(())
}
