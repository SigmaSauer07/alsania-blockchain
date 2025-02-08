use frame_support::{decl_module, decl_storage, decl_event, decl_error, dispatch};
use frame_system::ensure_signed;
use sp_runtime::traits::Hash;

#[cfg(test)]
mod mock;

#[cfg(test)]
mod tests;

pub trait Config: frame_system::Config {
    type Event: From<Event<Self>> + Into<<Self as frame_system::Config>::Event>;
}

decl_storage! {
    trait Store for Module<T: Config> as AlsaniaTokenModule {
        TotalSupply get(fn total_supply): u64;
        Balances get(fn balance_of): map hasher(blake2_128_concat) T::AccountId => u64;
    }
}

decl_event!(
    pub enum Event<T> where AccountId = <T as frame_system::Config>::AccountId {
        Transfer(AccountId, AccountId, u64),
    }
);

decl_error! {
    pub enum Error for Module<T: Config> {
        InsufficientBalance,
    }
}

decl_module! {
    pub struct Module<T: Config> for enum Call where origin: T::Origin {
        fn deposit_event() = default;

        #[weight = 10_000]
        pub fn transfer(origin, to: T::AccountId, value: u64) -> dispatch::DispatchResult {
            let sender = ensure_signed(origin)?;

            let sender_balance = Self::balance_of(&sender);
            let receiver_balance = Self::balance_of(&to);

            ensure!(sender_balance >= value, Error::<T>::InsufficientBalance);

            <Balances<T>>::insert(&sender, sender_balance - value);
            <Balances<T>>::insert(&to, receiver_balance + value);

            Self::deposit_event(RawEvent::Transfer(sender, to, value));
            Ok(())
        }
    }
}
