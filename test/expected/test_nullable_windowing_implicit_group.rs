use mimalloc::MiMalloc;
use renoir::prelude::*;
use serde::{Deserialize, Serialize};
use std::cmp::max;
use std::fs::File;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_0 {
    int1: Option<i64>,
    string1: Option<String>,
    int4: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_1 {
    int1: Option<i64>,
    string1: Option<String>,
    int4: Option<i64>,
    sum: i64,
    count: i64,
    group_mean: Option<f64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_2 {
    int1: Option<i64>,
    string1: Option<String>,
    int4: Option<i64>,
    sum: i64,
    count: i64,
    group_mean: Option<f64>,
    int4_demean: Option<f64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_collect {
    string1: Option<String>,
}

fn logic(ctx: StreamContext) {
    let var_0 = ctx
        .stream_csv::<Struct_var_0>("../data/nullable_op/ints_strings.csv")
        .batch_mode(BatchMode::fixed(16000));
    let var_2 = var_0
        .group_by(|x| x.string1.clone())
        .reduce_scan(
            |_, x| (x.int4.unwrap_or(0), 1),
            |_, (a_sum, a_count), (b_sum, b_count)| (a_sum + b_sum, a_count + b_count),
            |_, (sum, count), x| Struct_var_1 {
                int1: x.int1,
                string1: x.string1,
                int4: x.int4,
                sum: *sum,
                count: *count,
                group_mean: Some(*sum as f64 / *count as f64),
            },
        )
        .map(|(_, x)| Struct_var_2 {
            int1: x.int1,
            string1: x.string1,
            int4: x.int4,
            sum: x.sum,
            count: x.count,
            group_mean: x.group_mean,
            int4_demean: x.int4.zip(x.group_mean).map(|(a, b)| a as f64 - b as f64),
        });
    var_2
        .map(|(k, v)| (Struct_collect { string1: k.clone() }, v))
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
