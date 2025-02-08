#![cfg_attr(not(feature = "std"), no_std)]

pub mod module {
    // Define your runtime module logic here
    pub fn hello_runtime() {
        println!("Hello, Alsania Runtime!");
    }
}

mod alsc_token;

impl alsc_token::Config for Runtime {
    type Event = Event;
}

// ...existing code...

construct_runtime!(
    pub enum Runtime where
        Block = Block,
        NodeBlock = opaque::Block,
        UncheckedExtrinsic = UncheckedExtrinsic
    {
        // ...existing code...
        AlsaniaTokenModule: alsc_token::{Module, Call, Storage, Event<T>},
        // ...existing code...
    }
);
