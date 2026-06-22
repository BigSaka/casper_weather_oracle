#![cfg_attr(not(test), no_std)]
#![cfg_attr(not(test), no_main)]
extern crate alloc;

pub mod weather_oracle;
pub mod reputation;

pub use weather_oracle::{WeatherOracle, Metric, Reading};
pub use reputation::Reputation;
