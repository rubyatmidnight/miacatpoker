# MiacatPokerSystem

A provably fair poker system using SHA-512 hashing and cryptographic randomness for secure card distribution and verification.

## Overview

A provably fair poker system using SHA-512 hashing and cryptographic randomness for secure card distribution and verification.

## Features

- SHA-512 hashing for all operations
- Client seed commitments with salt
- Verifiable position assignments
- Secure card mapping and distribution
- Full hand evaluation and ranking for quick testing
- Independent verification system
- Support for up to 9 players
- Burns cards appropriately for Texas Hold'em format

## Features not included

- Turns, or interaction by each player
- Wagering, etc
- There is no waiting between draws; it fully generates a game state as an example
- No way to custom insert client seeds without editing the script

## Installation

```bash
git clone https://github.com/yourusername/MiacatPokerSystem
cd MiacatPokerSystem
pip install -r requirements.txt
```

## Usage

### Running a Demo Game

```bash
py miapoker.py
```

This will:
1. Generate a server seed and card mapping
2. Accept player commitments
3. Assign random positions
4. Deal cards in proper poker order
5. Show hands and board
6. Export game data for verification

### Verifying a Game

```bash
py miaverify.py
```

The verifier will:
1. Load game data from `game_data.json`
2. Verify all cryptographic commitments
3. Check player positions and dealing order
4. Validate all game operations
5. Allow players to verify the game_data json is unedited by letting them write in their client seed

## Game Data Format

The system exports game data in JSON format containing:
- Game ID and version
- Server seed and hashes
- Card mappings
- Player positions
- Client seeds and commitments
- Game state information

## Security Features

- Server seed remains secret until reveal
- Client seeds are protected by salt
- Position assignment uses double hashing
- Card distribution follows poker rules
- All operations are independently verifiable

## Version Support

Current version: 0.0.8
Supported versions to verify: 0.0.1 through 0.0.8

## License

This project is licensed under the AGPL License - see the [LICENSE](LICENSE) file for details.

## Notice

See [Notice](NOTICE)

## Technical Details

TBW

## Development Status

This is a demonstration implementation. While the cryptographic principles are sound, additional security auditing and ensuring a fair random probability distribution is achieved would be required for expanded use. 

## Contact

rubyatmidnight@proton.me
ruby@stakestats.net
