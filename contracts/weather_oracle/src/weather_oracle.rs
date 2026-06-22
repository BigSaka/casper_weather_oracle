//! Weather Oracle contract for the Casper Agentic Buildathon.
//!
//! A single off-chain agent wallet is authorized to post weather readings
//! (rainfall, wind speed, temperature) for a region. Each reading is checked
//! against a configurable threshold per metric; crossing it emits a
//! `TriggerFired` event that a parametric-insurance consumer contract (or
//! frontend) can watch for. A separate reconciliation step compares posted
//! readings against an official value after the fact and updates the
//! agent's accuracy score, which is what the dashboard's "trust score" is
//! built from.

use odra::prelude::*;
use odra::{Address, Var, Mapping, List};

/// The three metrics this MVP tracks. Stored as a u8 discriminant so it is
/// cheap to use as part of composite Mapping keys.
#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Metric {
    RainfallMm = 0,
    WindSpeedKmh = 1,
    TemperatureC = 2,
}

/// A single posted reading. Values are stored as i64 fixed-point
/// (value * 100) so the contract never has to deal with floats.
#[odra::odra_type]
pub struct Reading {
    pub metric: u8,
    pub value_fp: i64,
    pub timestamp: u64,
    pub source_confidence_bps: u32, // basis points, 0-10000
}

#[odra::event]
pub struct ReadingPosted {
    pub metric: u8,
    pub value_fp: i64,
    pub timestamp: u64,
}

#[odra::event]
pub struct TriggerFired {
    pub metric: u8,
    pub value_fp: i64,
    pub threshold_fp: i64,
    pub timestamp: u64,
}

#[odra::event]
pub struct OutcomeRecorded {
    pub reading_index: u32,
    pub official_value_fp: i64,
    pub was_accurate: bool,
}

#[odra::odra_error]
pub enum Error {
    NotAuthorizedAgent = 1,
    NotAuthorizedReconciler = 2,
    InvalidMetric = 3,
    ReadingNotFound = 4,
}

/// Core oracle: stores the agent's posted readings and fires trigger events
/// when a threshold is crossed.
#[odra::module(events = [ReadingPosted, TriggerFired])]
pub struct WeatherOracle {
    /// The only address allowed to call `submit_reading`.
    agent: Var<Address>,
    /// Per-metric trigger threshold, fixed-point (value * 100).
    thresholds_fp: Mapping<u8, i64>,
    /// Append-only history of readings, indexed by insertion order.
    readings: List<Reading>,
    /// Most recent reading per metric, for cheap dashboard reads.
    latest_by_metric: Mapping<u8, Reading>,
}

#[odra::module]
impl WeatherOracle {
    /// Deploy-time setup: register the agent wallet and starting thresholds.
    /// Threshold values are fixed-point (e.g. 5000 = 50.00mm).
    pub fn init(
        &mut self,
        agent: Address,
        rainfall_threshold_fp: i64,
        wind_speed_threshold_fp: i64,
        temperature_threshold_fp: i64,
    ) {
        self.agent.set(agent);
        self.thresholds_fp.set(&(Metric::RainfallMm as u8), rainfall_threshold_fp);
        self.thresholds_fp.set(&(Metric::WindSpeedKmh as u8), wind_speed_threshold_fp);
        self.thresholds_fp.set(&(Metric::TemperatureC as u8), temperature_threshold_fp);
    }

    /// Called by the agent on each scheduler tick. Stores the reading,
    /// updates the latest-value cache, and fires `TriggerFired` if the
    /// threshold for this metric is crossed.
    pub fn submit_reading(
        &mut self,
        metric: u8,
        value_fp: i64,
        timestamp: u64,
        source_confidence_bps: u32,
    ) {
        let caller = self.env().caller();
        if caller != self.agent.get_or_revert(&Error::NotAuthorizedAgent) {
            self.env().revert(Error::NotAuthorizedAgent);
        }
        if metric > Metric::TemperatureC as u8 {
            self.env().revert(Error::InvalidMetric);
        }

        let reading = Reading {
            metric,
            value_fp,
            timestamp,
            source_confidence_bps,
        };

        self.readings.push(reading.clone());
        self.latest_by_metric.set(&metric, reading.clone());

        self.env().emit_event(ReadingPosted {
            metric,
            value_fp,
            timestamp,
        });

        let threshold_fp = self.thresholds_fp.get_or_default(&metric);
        if value_fp >= threshold_fp {
            self.env().emit_event(TriggerFired {
                metric,
                value_fp,
                threshold_fp,
                timestamp,
            });
        }
    }

    /// Dashboard read: most recent reading for a given metric.
    pub fn get_latest_reading(&self, metric: u8) -> Option<Reading> {
        self.latest_by_metric.get(&metric)
    }

    /// Dashboard read: total number of readings ever posted, for paging
    /// through history with `get_reading_at`.
    pub fn reading_count(&self) -> u32 {
        self.readings.len()
    }

    /// Dashboard read: a single historical reading by index.
    pub fn get_reading_at(&self, index: u32) -> Option<Reading> {
        self.readings.get(index)
    }

    /// Admin/view: current trigger threshold for a metric.
    pub fn get_threshold(&self, metric: u8) -> i64 {
        self.thresholds_fp.get_or_default(&metric)
    }

    /// Admin/view: the registered agent address.
    pub fn get_agent(&self) -> Address {
        self.agent.get_or_default()
    }
}
