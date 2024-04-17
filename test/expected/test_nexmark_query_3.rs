use renoir::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs::File;
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_0 {
    id: Option<i64>,
    item_name: Option<String>,
    description: Option<String>,
    initial_bid: Option<i64>,
    reserve: Option<i64>,
    date_time: Option<i64>,
    expires: Option<i64>,
    seller: Option<i64>,
    category: Option<i64>,
    extra: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_1 {
    id: Option<i64>,
    name: Option<String>,
    email_address: Option<String>,
    credit_card: Option<String>,
    city: Option<String>,
    state: Option<String>,
    date_time: Option<i64>,
    extra: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_2 {
    id: Option<i64>,
    name: Option<String>,
    email_address: Option<String>,
    credit_card: Option<String>,
    city: Option<String>,
    state: Option<String>,
    date_time: Option<i64>,
    extra: Option<String>,
    id_right: Option<i64>,
    item_name: Option<String>,
    description: Option<String>,
    initial_bid: Option<i64>,
    reserve: Option<i64>,
    date_time_right: Option<i64>,
    expires: Option<i64>,
    seller: Option<i64>,
    category: Option<i64>,
    extra_right: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_var_3 {
    name: Option<String>,
    city: Option<String>,
    state: Option<String>,
    id: Option<i64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialOrd, PartialEq, Default)]
struct Struct_collect {
    seller: Option<i64>,
}

fn logic(ctx: StreamContext) {
    let var_0 = ctx.stream_csv::<Struct_var_0>(
        "/home/carlo/Projects/ibis-quickstart/data/nexmark/auction.csv",
    );
    let var_0 = var_0;
    let var_1 = ctx
        .stream_csv::<Struct_var_1>("/home/carlo/Projects/ibis-quickstart/data/nexmark/person.csv");
    let var_3 = var_1
        .join(var_0, |x| x.id.clone(), |y| y.seller.clone())
        .map(|(_, x)| Struct_var_2 {
            id: x.0.id,
            name: x.0.name,
            email_address: x.0.email_address,
            credit_card: x.0.credit_card,
            city: x.0.city,
            state: x.0.state,
            date_time: x.0.date_time,
            extra: x.0.extra,
            id_right: x.1.id,
            item_name: x.1.item_name,
            description: x.1.description,
            initial_bid: x.1.initial_bid,
            reserve: x.1.reserve,
            date_time_right: x.1.date_time,
            expires: x.1.expires,
            seller: x.1.seller,
            category: x.1.category,
            extra_right: x.1.extra,
        })
        .filter(|(_, x)| x.category.clone().is_some_and(|v| v == 10))
        .filter(|(_, x)| {
            x.state.clone().is_some_and(|v| v == "OR")
                | x.state.clone().is_some_and(|v| v == "ID")
                | x.state.clone().is_some_and(|v| v == "CA")
        })
        .map(|(_, x)| Struct_var_3 {
            name: x.name,
            city: x.city,
            state: x.state,
            id: x.id,
        });
    let out = var_3.collect_vec();
    tracing::info!("starting execution");
    ctx.execute_blocking();
    let out = out.get().unwrap();
    let out = out
        .iter()
        .map(|(k, v)| (Struct_collect { seller: k.clone() }, v))
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
