// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title ScrobblePay Splitter
/// @notice Distributes native USDC (Arc's native token) to many recipients in a
///         single transaction. Replaces the agent's N individual transfers.
/// @dev On Arc, USDC is the native token — there is no ERC-20 USDC contract — so
///      distribution uses native value transfers (`call{value:}`), not
///      `IERC20.transfer`. Arc requires EIP-1559 (type 0x2) txs.
contract Splitter {
    /// @notice Emitted once per successful distribution.
    event Distribution(
        address indexed caller,
        uint256 total,
        uint256 recipientCount,
        uint256 timestamp
    );

    /// @notice Accept native USDC deposits so the contract can be pre-funded.
    receive() external payable {}

    /// @notice Distribute native USDC to `recipients[i]` of `amounts[i]` each.
    /// @dev Payable: the caller may send the full total as `msg.value` in the same
    ///      tx, or rely on a previously deposited balance. Reverts on array length
    ///      mismatch, insufficient balance, or any failed transfer.
    function split(address[] calldata recipients, uint256[] calldata amounts)
        external
        payable
    {
        require(recipients.length == amounts.length, "length mismatch");

        uint256 total;
        for (uint256 i = 0; i < amounts.length; i++) {
            total += amounts[i];
        }
        require(total <= address(this).balance, "insufficient balance");

        for (uint256 i = 0; i < recipients.length; i++) {
            (bool ok, ) = recipients[i].call{value: amounts[i]}("");
            require(ok, "transfer failed");
        }

        emit Distribution(msg.sender, total, recipients.length, block.timestamp);
    }
}
