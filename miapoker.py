import hashlib
import secrets
import json
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

VERSION = "0.0.8"

class MiacatPokerSystem:
    gameVersion = VERSION
    MAX_PLAYERS = 9
    SUITS = [' of Hearts ♥', ' of Diamonds ♦', ' of Clubs ♣', ' of Spades ♠']
    VALUES = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
    
    def __init__(self, gameId: Optional[str] = None):
        self.gameId = gameId or secrets.token_hex(8)
        self.serverSeed = None
        self.serverHash = None
        self.doubleHash = None
        self.cardMapping = None
        self.clientSeeds: Dict[str, Dict[str, str]] = {}
        self.positions: Dict[str, int] = {}
        self.commitments: Dict[str, str] = {}
        self._initTimestamp = datetime.utcnow().isoformat()

    def exportGameData(self) -> Dict[str, Any]:
        return {
            "gameId": self.gameId,
            "gameVersion": self.gameVersion,
            "serverSeed": self.serverSeed,
            "serverHash": self.serverHash,
            "doubleHash": self.doubleHash,
            "cardMapping": self.cardMapping,
            "clientSeeds": self.clientSeeds,
            "positions": self.positions,
            "commitments": self.commitments
        }

    def hashValue(self, value: Any) -> str:
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value, sort_keys=True)
        if isinstance(value, str):
            value = value.encode('utf-8')
        return hashlib.sha512(value).hexdigest()

    def generateServerSeed(self) -> Dict[str, str]:
        self.serverSeed = secrets.token_hex(32)
        self.cardMapping = self._generateCardMapping()
        
        combinedSeed = f"MiacatPoker_{self.gameVersion}:{self.gameId}:{self.serverSeed}"
        combinedSeed += f":{json.dumps(self.cardMapping, sort_keys=True)}"
        
        self.serverHash = self.hashValue(combinedSeed)
        self.doubleHash = self.hashValue(self.serverHash)
        
        return {
            "gameId": self.gameId,
            "serverHash": self.serverHash,
            "doubleHash": self.doubleHash,
            "gameVersion": self.gameVersion
        }

    def _generateCardMapping(self) -> List[Dict[str, str]]:
        cards = []
        for suit in self.SUITS:
            for value in self.VALUES:
                cards.append({
                    "suit": suit,
                    "value": value,
                    "display": f"{value}{suit}"
                })
        return self._secureArrayShuffle(cards)

    def _secureArrayShuffle(self, items: List[Any]) -> List[Any]:
        items = items.copy()
        for i in range(len(items) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]
        return items

    def processClientSeed(self, playerId: str, clientSeed: str) -> Dict[str, str]:
        if len(self.clientSeeds) >= self.MAX_PLAYERS:
            raise ValueError(f"Maximum players ({self.MAX_PLAYERS}) reached!")
            
        if len(clientSeed.encode('utf-8')) > 64:
            raise ValueError("Client seed too long (max 64 bytes when UTF-8 encoded)")
            
        salt = secrets.token_hex(16)
        commitmentString = f"MiacatPoker_{self.gameVersion}:{self.gameId}:{clientSeed}:{salt}"
        commitment = self.hashValue(commitmentString)
        
        self.clientSeeds[playerId] = {"seed": clientSeed, "salt": salt}
        self.commitments[playerId] = commitment
        
        return {
            "playerId": playerId.lower,
            "commitment": commitment,
            "salt": salt
        }

    def assignPositions(self) -> Dict[str, int]:
        if not self.clientSeeds or not self.doubleHash:
            raise ValueError("Need client seeds and server hash before assigning positions!")
            
        playerIds = list(self.clientSeeds.keys())
        positions = list(range(1, len(playerIds) + 1))
        
        entropy = int(self.doubleHash[:16], 16)
        positionSeed = f"positions_{self.gameId}_{entropy}"
        
        shuffled = self._secureArrayShuffle(positions)
        
        self.positions = {
            playerId: pos 
            for playerId, pos in zip(sorted(playerIds), shuffled)
        }
        
        return self.positions.copy()

    def generateDeck(self) -> List[Dict[str, str]]:
        if not all([self.serverSeed, self.cardMapping, self.positions, self.clientSeeds]):
            raise ValueError("Missing required game state!")
            
        seeds = []
        for playerId, pos in sorted(self.positions.items()):
            clientData = self.clientSeeds[playerId]
            seeds.append(f"{clientData['seed']}:{pos}")
            
        finalSeed = (
            f"MiacatPoker_{self.gameVersion}:{self.gameId}:"
            f"{self.serverSeed}:{':'.join(seeds)}"
        )
        
        deckHash = self.hashValue(finalSeed)
        numbers = list(range(52))
        finalOrder = self._secureArrayShuffle(numbers)
        
        return [self.cardMapping[i] for i in finalOrder]

def dealCards(game, deck, numPlayers, playerByPosition):
    cardDrawn = 0
    
    print("\n🔥🎴 Burning first card...")
    cardDrawn += 1
    
    # First round of cards
    print("\n🎴 First round of dealing:")
    for position in list(range(2, numPlayers + 1)) + [1]:  # Start at 2, wrap to 1 (dealer)
        player = playerByPosition[position]
        print(f"Position {position} ({player}): ", [card['display'] for card in deck[cardDrawn:cardDrawn+1]])
        cardDrawn += 1
    
    # Second round of cards
    print("\n🎴🎴 Second round of dealing:")
    for position in list(range(2, numPlayers + 1)) + [1]:
        player = playerByPosition[position]
        print(f"Position {position} ({player}): ", [card['display'] for card in deck[cardDrawn:cardDrawn+1]])
        cardDrawn += 1
    
    # Community cards with burns
    print("\n🔥🎴 Burning card before flop...")
    cardDrawn += 1
    
    print("\n🎴🎴🎴 Flop: ", [card['display'] for card in deck[cardDrawn:cardDrawn+3]])
    cardDrawn += 3
    
    print("\n🔥🎴 Burning card before turn...")
    cardDrawn += 1
    
    print("\n🎴🎴🎴🎴 Turn: ", [card['display'] for card in deck[cardDrawn:cardDrawn+1]])
    cardDrawn += 1
    
    print("\n🔥🎴 Burning card before river...")
    cardDrawn += 1
    
    print("\n🎴🎴🎴🎴🎴 River: ", [card['display'] for card in deck[cardDrawn:cardDrawn+1]])

class PokerHandEvaluator:
    HAND_RANKS = {
        'Royal Flush': 10,
        'Straight Flush': 9,
        'Four of a Kind': 8,
        'Full House': 7,
        'Flush': 6,
        'Straight': 5,
        'Three of a Kind': 4,
        'Two Pair': 3,
        'One Pair': 2,
        'High Card': 1
    }
    
    CARD_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
        '10': 10, 'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
    }

    def evaluateHand(self, holeCards, communityCards):
        allCards = holeCards + communityCards
        values = [card['value'] for card in allCards]
        suits = [card['suit'] for card in allCards]
        
        # Convert card values to numbers
        numericValues = [self.CARD_VALUES[val] for val in values]
        numericValues.sort(reverse=True)
        
        # Check for each hand type
        if self._isRoyalFlush(numericValues, suits):
            return ('Royal Flush', numericValues[:5])
        if self._isStraightFlush(numericValues, suits):
            return ('Straight Flush', numericValues[:5])
        if self._isFourOfKind(numericValues):
            return ('Four of a Kind', numericValues[:4])
        if self._isFullHouse(numericValues):
            return ('Full House', numericValues[:5])
        if self._isFlush(suits):
            return ('Flush', numericValues[:5])
        if self._isStraight(numericValues):
            return ('Straight', numericValues[:5])
        if self._isThreeOfKind(numericValues):
            return ('Three of a Kind', numericValues[:3])
        if self._isTwoPair(numericValues):
            return ('Two Pair', numericValues[:4])
        if self._isOnePair(numericValues):
            return ('One Pair', numericValues[:2])
        
        return ('High Card', numericValues[:1])

    def _isRoyalFlush(self, values, suits):
        return self._isStraightFlush(values, suits) and max(values) == 14

    def _isStraightFlush(self, values, suits):
        return self._isFlush(suits) and self._isStraight(values)

    def _isFourOfKind(self, values):
        return any(values.count(val) == 4 for val in set(values))

    def _isFullHouse(self, values):
        return self._isThreeOfKind(values) and self._isOnePair(values)

    def _isFlush(self, suits):
        return any(suits.count(suit) >= 5 for suit in set(suits))

    def _isStraight(self, values):
        unique_values = sorted(list(set(values)), reverse=True)
        if len(unique_values) >= 5:
            for i in range(len(unique_values) - 4):
                if unique_values[i] - unique_values[i + 4] == 4:
                    return True
        # Check Ace-low straight
        if set([14, 2, 3, 4, 5]).issubset(set(values)):
            return True
        return False

    def _isThreeOfKind(self, values):
        return any(values.count(val) >= 3 for val in set(values))

    def _isTwoPair(self, values):
        pairs = sum(1 for val in set(values) if values.count(val) >= 2)
        return pairs >= 2

    def _isOnePair(self, values):
        return any(values.count(val) >= 2 for val in set(values))
    

def showGameResults(deck, playerPositions, playerByPosition, numPlayers):
    evaluator = PokerHandEvaluator()
    playerHands = {}
    cardIndex = 1  # Skip first burn card
    
    # Collect hole cards
    for round in range(2):
        for position in list(range(2, numPlayers + 1)) + [1]:
            player = playerByPosition[position]
            if player not in playerHands:
                playerHands[player] = []
            playerHands[player].append(deck[cardIndex])
            cardIndex += 1
    
    # Skip burn card before flop
    cardIndex += 1
    
    # Get flop
    flop = deck[cardIndex:cardIndex+3]
    cardIndex += 3
    
    # Skip burn, get turn
    cardIndex += 1
    turn = deck[cardIndex:cardIndex+1]
    cardIndex += 1
    
    # Skip burn, get river
    cardIndex += 1
    river = deck[cardIndex:cardIndex+1]
    
    board = flop + turn + river
    
    # Evaluate each hand
    results = []
    print("\n🎴 Final Game Results 🎴")
    print("\n📋 Community Cards:")
    print("Board:", [card['display'] for card in board])
    
    print("\n👥 Player Hands:")
    for player, holeCards in playerHands.items():
        position = playerPositions[player]
        handType, handCards = evaluator.evaluateHand(holeCards, board)
        print(f"Position {position} ({player}):")
        print(f"  Hole cards: {[card['display'] for card in holeCards]}")
        print(f"  Hand: {handType}")
        results.append((player, position, handType, handCards, holeCards))
    
    # Sort by hand strength
    results.sort(key=lambda x: (
        evaluator.HAND_RANKS[x[2]], 
        x[3]
    ), reverse=True)
    
    print("\nRound Result:")
    for i, (player, position, handType, handCards, _) in enumerate(results, 1):
        print(f"{i}. Position {position} ({player}) - {handType}")




def demoGame():
    print("Starting MiacatPokerSystem demonstration")
    game = MiacatPokerSystem()
    
    initData = game.generateServerSeed()
    print("~~~~~")
    print(f"\nGame ID: {initData['gameId']}")
    print("~~~~~")
    print(f"Server Hash: {initData['serverHash'][:20]}...")
    print(f"Position Hash: {initData['doubleHash'][:20]}...")
    print("")
    print("")
    print("Game simulating:")

    players = ["Seal", "Syztmz", "Eddie", "Wino"]
    for player in players:
        result = game.processClientSeed(player, f"secret_seed_{player}")
        print(f"{player}'s commitment: {result['commitment'][:20]}...")
    
    positions = game.assignPositions()
    print("\n Player Positions:")
    for player, pos in positions.items():
        print(f"{player} -> Position {pos}")
        
    playerByPosition = {pos: player for player, pos in positions.items()}
    
    deck = game.generateDeck()
    dealCards(game, deck, len(players), playerByPosition)
    showGameResults(deck, positions, playerByPosition, len(players)) 

    with open('game_data.json', 'w') as f:
        json.dump(game.exportGameData(), f, indent=2)

if __name__ == "__main__":
    demoGame()
