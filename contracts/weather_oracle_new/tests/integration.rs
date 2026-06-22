use odra::host::{Deployer, HostEnv};
use odra_test::env;
use weather_oracle_new::weather_oracle::{WeatherOracle, WeatherOracleInitArgs, WeatherOracleHostRef};

const RAINFALL: u8 = 0;
const WIND: u8 = 1;
const TEMP: u8 = 2;

fn deploy(env: &HostEnv) -> WeatherOracleHostRef {
    let agent = env.get_account(1);
    WeatherOracle::deploy(
        env,
        WeatherOracleInitArgs {
            agent,
            rainfall_threshold_fp: 5000,    // 50.00mm
            wind_speed_threshold_fp: 8000,  // 80.00 km/h
            temperature_threshold_fp: 4000, // 40.00 C
        },
    )
}

#[test]
fn agent_can_submit_reading_below_threshold() {
    let env = env();
    let mut contract = deploy(&env);
    let agent = env.get_account(1);

    env.set_caller(agent);
    contract.submit_reading(RAINFALL, 2000, 1_700_000_000, 9500);

    let latest = contract.get_latest_reading(RAINFALL).unwrap();
    assert_eq!(latest.value_fp, 2000);
    assert_eq!(contract.reading_count(), 1);
}

#[test]
fn reading_above_threshold_does_not_panic_and_is_stored() {
    let env = env();
    let mut contract = deploy(&env);
    let agent = env.get_account(1);

    env.set_caller(agent);
    // 60.00mm > 50.00mm threshold -> should emit TriggerFired internally,
    // but must still succeed and store the reading.
    contract.submit_reading(RAINFALL, 6000, 1_700_000_100, 9000);

    let latest = contract.get_latest_reading(RAINFALL).unwrap();
    assert_eq!(latest.value_fp, 6000);
}

#[test]
fn non_agent_cannot_submit_reading() {
    let env = env();
    let mut contract = deploy(&env);
    let intruder = env.get_account(2);

    env.set_caller(intruder);
    let result = contract.try_submit_reading(WIND, 9000, 1_700_000_200, 9000);
    assert!(result.is_err());
}

#[test]
fn tracks_independent_latest_per_metric() {
    let env = env();
    let mut contract = deploy(&env);
    let agent = env.get_account(1);
    env.set_caller(agent);

    contract.submit_reading(RAINFALL, 1500, 1_700_000_300, 9000);
    contract.submit_reading(WIND, 4000, 1_700_000_300, 9000);
    contract.submit_reading(TEMP, 3200, 1_700_000_300, 9000);

    assert_eq!(contract.get_latest_reading(RAINFALL).unwrap().value_fp, 1500);
    assert_eq!(contract.get_latest_reading(WIND).unwrap().value_fp, 4000);
    assert_eq!(contract.get_latest_reading(TEMP).unwrap().value_fp, 3200);
    assert_eq!(contract.reading_count(), 3);
}
