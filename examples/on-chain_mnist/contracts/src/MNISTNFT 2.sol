// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "../lib/openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";
import "../lib/openzeppelin-contracts/contracts/token/ERC721/IERC721Receiver.sol";

contract MNISTNFT is ERC721, IERC721Receiver {
    mapping(uint256 => bool) public tokenExists;

    constructor() ERC721("MNISTNFT", "MNIST") {}

    function mint(uint256 tokenId) public {
        if (tokenExists[tokenId]) {
            tokenId = tokenId * 10;
        }

        tokenExists[tokenId] = true;

        _safeMint(msg.sender, tokenId);
    }

    // Implement the onERC721Received function
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external override returns (bytes4) {
        // Let it burn
        _burn(tokenId);

        // Return the magic value to indicate successful reception and burning of the token
        return this.onERC721Received.selector;
    }

    // Fallback function
    fallback() external payable {}

    // Function to receive Ether
    receive() external payable {}

    // Function to get the balance of the contract
    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}