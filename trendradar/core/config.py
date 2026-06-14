# coding=utf-8
"""
Configuration tool module - multi-account configuration analysis and verification

Provides parsing, verification and restriction functions for multi-account push configurations
"""

from typing import Dict, List, Optional, Tuple


def parse_multi_account_config(config_value: str, separator: str = ";") -> List[str]:
    """
    Parse multi-account configuration and return account list

    Args:
        config_value: Configuration value string, multiple accounts are separated by delimiters
        separator: separator, default is ;

    Returns:
        Account list, empty string will be reserved (used for placeholder)

    Examples:
        >>> parse_multi_account_config("url1;url2;url3")
        ['url1', 'url2', 'url3']
        >>> parse_multi_account_config(";token2") # The first account has no token
        ['', 'token2']
        >>> parse_multi_account_config("")
        []
    """
    if not config_value:
        return []
    # Reserve the empty string for placeholder (such as ";token2" means the first account has no token)
    accounts = [acc.strip() for acc in config_value.split(separator)]
    # Filter out all empty cases
    if all(not acc for acc in accounts):
        return []
    return accounts


def validate_paired_configs(
    configs: Dict[str, List[str]],
    channel_name: str,
    required_keys: Optional[List[str]] = None
) -> Tuple[bool, int]:
    """
    Verify that the number of paired configurations is consistent

    For channels that require pairing of multiple configuration items (such as Telegram’s token and chat_id),
    Verify that the number of accounts for all configuration items is consistent.

    Args:
        configs: configuration dictionary, key is the configuration name, value is the account list
        channel_name: channel name, used for log output
        required_keys: list of configuration items that must have values

    Returns:
        (Whether the verification is passed, the number of accounts)

    Examples:
        >>> validate_paired_configs({
        ...     "token": ["t1", "t2"],
        ...     "chat_id": ["c1", "c2"]
        ... }, "Telegram", ["token", "chat_id"])
        (True, 2)

        >>> validate_paired_configs({
        ...     "token": ["t1", "t2"],
        ... "chat_id": ["c1"] # The quantity does not match
        ... }, "Telegram", ["token", "chat_id"])
        (False, 0)
    """
    # Filter out empty lists
    non_empty_configs = {k: v for k, v in configs.items() if v}

    if not non_empty_configs:
        return True, 0

    # Check required items
    if required_keys:
        for key in required_keys:
            if key not in non_empty_configs or not non_empty_configs[key]:
                return True, 0 # If the required item is empty, it is regarded as not configured.

    # Get the length of all non-empty configurations
    lengths = {k: len(v) for k, v in non_empty_configs.items()}
    unique_lengths = set(lengths.values())

    if len(unique_lengths) > 1:
        print(f"❌ {channel_name} configuration error: the number of paired configurations is inconsistent, the channel push will be skipped")
        for key, length in lengths.items():
            print(f" - {key}: {length} ")
        return False, 0

    return True, list(unique_lengths)[0] if unique_lengths else 0


def limit_accounts(
    accounts: List[str],
    max_count: int,
    channel_name: str
) -> List[str]:
    """
    Limit the number of accounts

    When the number of configured accounts exceeds the maximum limit, only the first N accounts will be used.
    and output a warning message.

    Args:
        accounts: account list
        max_count: maximum number of accounts
        channel_name: channel name, used for log output

    Returns:
        Restricted account list

    Examples:
        >>> limit_accounts(["a1", "a2", "a3"], 2, "Feishu")
        ⚠️ Feishu has configured 3 accounts, which exceeds the maximum limit of 2. Only the first 2 are used.
        ['a1', 'a2']
    """
    if len(accounts) > max_count:
        print(f"⚠️ {channel_name} is configured with {len(accounts)} accounts, exceeding the maximum limit {max_count}, only the first {max_count} will be used")
        print(f" ⚠️ Warning: If you are a fork user, too many accounts may cause GitHub Actions to run for too long, posing account risks")
        return accounts[:max_count]
    return accounts


def get_account_at_index(accounts: List[str], index: int, default: str = "") -> str:
    """
    Safely obtain the account value of the specified index

    When the index is out of range or the account value is empty, the default value is returned.

    Args:
        accounts: account list
        index: index
        default: default value

    Returns:
        Account value or default value

    Examples:
        >>> get_account_at_index(["a", "b", "c"], 1)
        'b'
        >>> get_account_at_index(["a", "", "c"], 1, "default")
        'default'
        >>> get_account_at_index(["a"], 5, "default")
        'default'
    """
    if index < len(accounts):
        return accounts[index] if accounts[index] else default
    return default
