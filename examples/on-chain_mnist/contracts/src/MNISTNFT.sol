// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "../lib/openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";

contract MNISTNFT is ERC721 {
    mapping(uint256 => bool) public tokenExists;

    constructor() ERC721("MNISTNFT", "MNIST") {}

    function mint(uint256 tokenId) public {
        require(!tokenExists[tokenId], "Token already minted!");

        if (tokenExists[tokenId]) {
            tokenId = tokenId * 10;
        }

        tokenExists[tokenId] = true;

        _safeMint(msg.sender, tokenId);
    }
    
    // Not secure; anyone can withdraw
    function withdraw() public {
        (bool success, ) = msg.sender.call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }
}