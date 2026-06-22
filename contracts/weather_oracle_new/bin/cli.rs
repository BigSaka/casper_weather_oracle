//! CLI tool for deploying and interacting with the WeatherOracle and Reputation contracts.
use weather_oracle_new::weather_oracle::{WeatherOracle, WeatherOracleInitArgs};
use weather_oracle_new::reputation::{Reputation, ReputationInitArgs};
use odra::host::HostEnv;
use odra_cli::{
    deploy::DeployScript,
    DeployedContractsContainer, DeployerExt,
    OdraCli,
};

pub struct WeatherOracleDeployScript;
impl DeployScript for WeatherOracleDeployScript {
    fn deploy(
        &self,
        env: &HostEnv,
        container: &mut DeployedContractsContainer
    ) -> Result<(), odra_cli::deploy::Error> {
        let _oracle = WeatherOracle::load_or_deploy(
            &env,
            WeatherOracleInitArgs {
                agent: env.caller(),
                rainfall_threshold_fp: 5000,
                wind_speed_threshold_fp: 8000,
                temperature_threshold_fp: 4000,
            },
            container,
            350_000_000_000
        )?;
        let _reputation = Reputation::load_or_deploy(
            &env,
            ReputationInitArgs {
                reconciler: env.caller(),
                tolerance_fp: 200,
            },
            container,
            350_000_000_000
        )?;
        Ok(())
    }
}

pub fn main() {
    OdraCli::new()
        .about("CLI tool for WeatherOracle and Reputation contracts")
        .deploy(WeatherOracleDeployScript)
        .contract::<WeatherOracle>()
        .contract::<Reputation>()
        .build()
        .run();
}
