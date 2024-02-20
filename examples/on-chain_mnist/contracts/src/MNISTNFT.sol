// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MNISTNFT is ERC721, Ownable {

    uint256 public mintPrice = 0.05 ether;

    mapping(uint256 => bool) public tokenExists;

    constructor() ERC721("MNISTNFT", "NFT") {}

    function mint(uint256 tokenId) public payable {
        require(msg.value == mintPrice, "Incorrect mint price");
        require(!tokenExists[tokenId], "Token already minted");

        if (tokenExists[tokenId]) {
            tokenId = tokenId * 10;
        }

        tokenExists[tokenId] = true;
        
        _safeMint(msg.sender, tokenId);
    }

    function withdraw() public onlyOwner {
        (bool success, ) = msg.sender.call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }
}