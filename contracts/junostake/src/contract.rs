use crate::error::ContractError;
use crate::msg::{CompPrefsWithAddresses, ExecuteMsg, InstantiateMsg, JunostakeCompoundPrefs, QueryMsg};
use crate::state::{ADMIN, AUTHORIZED_ADDRS, PROJECT_ADDRS};
use crate::{execute, queries};
#[cfg(not(feature = "library"))]
use cosmwasm_std::entry_point;
use cosmwasm_std::{to_binary, Binary, Deps, DepsMut, Env, MessageInfo, Response, StdError, StdResult};
use cw2::{get_contract_version, set_contract_version};
use cw_grant_spec::grantable_trait::{GrantStructure, Grantable};
use semver::Version;

// version info for migration info
const CONTRACT_NAME: &str = "crates.io:ac-outpost-junostake";
const CONTRACT_VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg_attr(not(feature = "library"), entry_point)]
#[cfg_attr(feature = "interface", cw_orch::interface_entry_point)]
pub fn instantiate(deps: DepsMut, _env: Env, info: MessageInfo, msg: InstantiateMsg) -> Result<Response, ContractError> {
    cw2::set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;

    let InstantiateMsg {
        admin,
        project_addresses,
    } = msg;

    let admin_addr = match admin {
        Some(admin) => deps
            .api
            .addr_validate(&admin)
            .map_err(|_| ContractError::InvalidAuthorizedAddress(admin.to_string()))?,
        None => info.sender,
    };

    ADMIN.save(deps.storage, &admin_addr)?;
    AUTHORIZED_ADDRS.save(deps.storage, &vec![])?;
    PROJECT_ADDRS.save(deps.storage, &project_addresses)?;

    Ok(Response::default())
}

#[cfg_attr(not(feature = "library"), entry_point)]
#[cfg_attr(feature = "interface", cw_orch::interface_entry_point)]
pub fn migrate(deps: DepsMut, _env: Env, _msg: InstantiateMsg) -> Result<Response, ContractError> {
    let version: Version = CONTRACT_VERSION.parse()?;
    let storage_version: Version = get_contract_version(deps.storage)?.version.parse()?;

    if storage_version < version {
        set_contract_version(deps.storage, CONTRACT_NAME, CONTRACT_VERSION)?;
    }
    Ok(Response::default())
}

#[cfg_attr(not(feature = "library"), entry_point)]
#[cfg_attr(feature = "interface", cw_orch::interface_entry_point)]
pub fn execute(deps: DepsMut, env: Env, info: MessageInfo, msg: ExecuteMsg) -> Result<Response, ContractError> {
    match msg {
        ExecuteMsg::AddAuthorizedCompounder(address) => {
            if info.sender != ADMIN.load(deps.storage)? {
                return Err(ContractError::Unauthorized {});
            }
            let authorized_addr = deps
                .api
                .addr_validate(&address)
                .map_err(|_| ContractError::InvalidAuthorizedAddress(address.to_string()))?;

            AUTHORIZED_ADDRS.update(deps.storage, |mut addrs| {
                if addrs.contains(&authorized_addr) {
                    Err(ContractError::DuplicateAuthorizedAddress(authorized_addr.to_string()))
                } else {
                    addrs.push(authorized_addr.clone());
                    Ok(addrs)
                }
            })?;

            Ok(Response::default())
        }
        ExecuteMsg::RemoveAuthorizedCompounder(address) => {
            if info.sender != ADMIN.load(deps.storage)? {
                return Err(ContractError::Unauthorized {});
            }
            let authorized_addr = deps
                .api
                .addr_validate(&address)
                .map_err(|_| ContractError::InvalidAuthorizedAddress(address.to_string()))?;

            AUTHORIZED_ADDRS.update(deps.storage, |mut addrs| -> Result<_, StdError> {
                addrs.retain(|x| x != authorized_addr);
                Ok(addrs)
            })?;

            Ok(Response::default())
        }
        ExecuteMsg::Compound(JunostakeCompoundPrefs {
            delegator_address,
            comp_prefs,
            tax_fee,
        }) => {
            let addresses = PROJECT_ADDRS.load(deps.storage)?;

            execute::compound(deps, env, info, addresses, delegator_address, comp_prefs, tax_fee)
        }
    }
}

#[cfg_attr(not(feature = "library"), entry_point)]
#[cfg_attr(feature = "interface", cw_orch::interface_entry_point)]
pub fn query(deps: Deps, env: Env, msg: QueryMsg) -> StdResult<Binary> {
    match msg {
        QueryMsg::Version {} => to_binary(&queries::query_version()),
        QueryMsg::AuthorizedCompounders {} => to_binary(&queries::query_authorized_compounders(deps)),
        QueryMsg::GrantSpec { comp_prefs, expiration } => {
            let project_addresses = PROJECT_ADDRS.load(deps.storage)?;
            to_binary(&QueryMsg::query_grants(GrantStructure {
                grantee: env.contract.address.clone(),
                granter: deps.api.addr_validate(&comp_prefs.delegator_address)?,
                expiration,
                grant_contract: env.contract.address,
                grant_data: CompPrefsWithAddresses {
                    comp_prefs,
                    project_addresses,
                },
            }))
        }
    }
}
