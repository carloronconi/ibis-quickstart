use mimalloc::MiMalloc;
use renoir::prelude::*;
use serde::{Deserialize, Serialize};
use std::cmp::max;
use std::fs::File;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_0 {
    fruit: String,
    weight: i64,
    price: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_1 {
    fruit: String,
    weight: i64,
    price: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_2 {
    fruit: Option<String>,
    weight: Option<i64>,
    price: Option<i64>,
    fruit_right: Option<String>,
    weight_right: Option<i64>,
    price_right: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_collect {
    fruit: String,
}

fn logic(ctx: StreamContext) {
    let var_0 = ctx
        .stream_csv::<Struct_var_0>("../data/non_nullable_op/fruit_right.csv")
        .batch_mode(BatchMode::fixed(16000));
    let var_0 = var_0;
    let var_1 = ctx
        .stream_csv::<Struct_var_1>("../data/non_nullable_op/fruit_left.csv")
        .batch_mode(BatchMode::fixed(16000));
    let var_2 = var_1
        .outer_join(var_0, |x| x.fruit.clone(), |y| y.fruit.clone())
        .map(|(_, x)| {
            let mut v = Struct_var_2 {
                fruit: None,
                weight: None,
                price: None,
                fruit_right: None,
                weight_right: None,
                price_right: None,
            };
            if let Some(i) = x.0 {
                v.fruit = Some(i.fruit);
                v.weight = Some(i.weight);
                v.price = i.price;
            };
            if let Some(i) = x.1 {
                v.fruit_right = Some(i.fruit);
                v.weight_right = Some(i.weight);
                v.price_right = i.price;
            };
            v
        });
    var_2
        .map(|(k, v)| (Struct_collect { fruit: k.clone() }, v))
        .drop_key()
        .write_csv_one("../out/noir-result.csv", true);
    File::create("../out/noir-result.csv").unwrap();
    tracing::info!("starting execution");
    ctx.execute_blocking();
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
