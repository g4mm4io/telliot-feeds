// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

interface IFetch {
    function submitValue(
        bytes32 _queryId,
        bytes calldata _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external;

    function getAddressVars(bytes32 _data) external view returns (address);

    function depositStake() external;

    function requestStakingWithdraw() external;

    function getCurrentReward(
        bytes32 _queryId
    ) external view returns (uint256, uint256);

    function transfer(
        address _to,
        uint256 _amount
    ) external returns (bool success);

    function withdrawStake() external;
}

contract Reporter {
    IFetch public fetch;
    IFetch public oracle;
    address public owner;
    uint256 public profitThreshold; //inFETCH

    constructor(
        address _fetchAddress,
        address _oracleAddress,
        uint256 _profitThreshold
    ) {
        fetch = IFetch(_fetchAddress);
        oracle = IFetch(_oracleAddress); //keccak256(_ORACLE_CONTRACT)
        owner = msg.sender;
        profitThreshold = _profitThreshold;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function changeOwner(address _newOwner) external onlyOwner {
        owner = _newOwner;
    }

    function depositStake() external onlyOwner {
        fetch.depositStake();
    }

    function requestStakingWithdraw() external onlyOwner {
        fetch.requestStakingWithdraw();
    }

    function submitValue(
        bytes32 _queryId,
        bytes memory _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external onlyOwner {
        uint256 _reward;
        (, _reward) = oracle.getCurrentReward(_queryId);
        require(_reward > profitThreshold, "profit threshold not met");
        oracle.submitValue(_queryId, _value, _nonce, _queryData);
    }

    function submitValueBypass(
        bytes32 _queryId,
        bytes memory _value,
        uint256 _nonce,
        bytes memory _queryData
    ) external onlyOwner {
        oracle.submitValue(_queryId, _value, _nonce, _queryData);
    }

    function transfer(address _to, uint256 _amount) external onlyOwner {
        fetch.transfer(_to, _amount);
    }

    function withdrawStake() external onlyOwner {
        fetch.withdrawStake();
    }
}
