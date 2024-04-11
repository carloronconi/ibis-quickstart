use renoir::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::File;
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_var_0 {
    fruit: String,
    weight: i64,
    price: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_var_1 {
    fruit: String,
    weight: i64,
    price: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_var_2 {
    agg2: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_var_3 {
    agg2: Option<i64>,
    fruit: Option<String>,
    weight: Option<i64>,
    price: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_var_4 {
    agg2: Option<i64>,
    fruit: Option<String>,
    weight: Option<i64>,
    price: Option<i64>,
    mut4: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, Ord, PartialOrd, Eq, PartialEq, Default)]
struct Struct_collect {
    fruit: String,
}

fn logic(ctx: StreamContext) {
    let var_0 =
        ctx.stream_csv::<Struct_var_0>("/home/carlo/Projects/ibis-quickstart/data/fruit_left.csv");
    let var_0 = var_0;
    let var_1 =
        ctx.stream_csv::<Struct_var_1>("/home/carlo/Projects/ibis-quickstart/data/fruit_right.csv");
    let var_4 = var_1
        .group_by(|x| x.fruit.clone())
        .reduce(|a, b| a.weight = a.weight + b.weight)
        .map(|(_, x)| Struct_var_2 {
            agg2: Some(x.weight),
        })
        .join(var_0.group_by(|x| x.fruit.clone()))
        .map(|(_, x)| Struct_var_3 {
            agg2: x.0.agg2,
            fruit: Some(x.1.fruit),
            weight: Some(x.1.weight),
            price: x.1.price,
        })
        .map(|(_, x)| Struct_var_4 {
            agg2: x.agg2,
            fruit: x.fruit,
            weight: x.weight,
            price: x.price,
            mut4: x.price.map(|v| v + 100),
        });
    let out = var_4.collect_vec();
    tracing::info!("starting execution");
    ctx.execute_blocking();
    let out = out.get().unwrap();
    let out = out
        .iter()
        .map(|(k, v)| (Struct_collect { fruit: k.clone() }, v))
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