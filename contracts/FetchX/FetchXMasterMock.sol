// SPDX-Licence-Identifier: MIT
pragma solidity ^0.8.10;

contract FetchXMasterMock {
    function getStakerInfo(
        address _staker
    ) external view returns (uint256, uint256) {
        return (uint256(1), uint256(123456789));
    }
}
