import hashlib
import json
from typing import Dict, List, Any
from packaging import version

VERIFIER_VERSION = "0.0.1"
VERSION = "0.0.2" # the current version of the game when this verifier was published.
supportedVersions = ['0.0.1', '0.0.8']

class MiacatVerifier:

    SUITS = [' of Hearts ♥', ' of Diamonds ♦', ' of Clubs ♣', ' of Spades ♠']
    VALUES = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']

    def __init__(self, gameData: Dict[str, Any]):
        self.gameId = gameData['gameId']
        self.serverSeed = gameData['serverSeed']
        self.serverHash = gameData['serverHash']
        self.doubleHash = gameData['doubleHash']
        self.cardMapping = gameData['cardMapping']
        self.clientSeeds = gameData['clientSeeds']
        self.positions = gameData['positions']
        self.commitments = gameData['commitments']
        self.gameVersion = gameData['gameVersion']
        
    def hashValue(self, value: Any) -> str:
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value, sort_keys=True)
        if isinstance(value, str):
            value = value.encode('utf-8')
        return hashlib.sha512(value).hexdigest()
    
    def verifyServerHash(self) -> bool:
        combinedSeed = f"MiacatPoker_{self.gameVersion}:{self.gameId}:{self.serverSeed}"
        combinedSeed += f":{json.dumps(self.cardMapping, sort_keys=True)}"
        calculatedHash = self.hashValue(combinedSeed)
        return calculatedHash == self.serverHash
    
    def verifyDoubleHash(self) -> bool:
        calculatedDoubleHash = self.hashValue(self.serverHash)
        return calculatedDoubleHash == self.doubleHash
    
    def verifyPlayerCommitment(self, playerId: str) -> bool:
        data = self.clientSeeds[playerId]
        commitmentString = f"MiacatPoker_{self.gameVersion}:{self.gameId}:{data['seed']}:{data['salt']}"
        calculatedCommitment = self.hashValue(commitmentString)
        return calculatedCommitment == self.commitments[playerId]
    
    def checkVersion(self):
        try:
            gameVer = str(self.gameVersion).strip()
            if any(gameVer == str(v).strip() for v in supportedVersions):
                return True
            else:
                print(f"Version {self.gameVersion} is not supported. This verifier supports versions: {', '.join(supportedVersions)}")
                return False
        except Exception:
            print(f"Version {self.gameVersion} is not supported. This verifier supports versions: {', '.join(supportedVersions)}")
            return False
    
    def verifyDeck(self) -> bool:
        try:
            self.regenerateDeck()
            return True
        except Exception:
            return False
    
    def regenerateDeck(self) -> str:
        seeds = []
        for playerId, pos in sorted(self.positions.items()):
            clientData = self.clientSeeds[playerId]
            seeds.append(f"{clientData['seed']}:{pos}")
            
        finalSeed = (
            f"MiacatPoker_{self.gameVersion}:{self.gameId}:"
            f"{self.serverSeed}:{':'.join(seeds)}"
        )
        return self.hashValue(finalSeed)
        
    def verifyGame(self) -> Dict[str, bool]:
        results = {
            "serverHashValid": self.verifyServerHash(),
            "checkVersionValid": self.checkVersion(),
            "doubleHashValid": self.verifyDoubleHash(),
            "commitmentValid": {},
            "deckValid": self.verifyDeck()
        }
        
        for playerId in self.clientSeeds:
            results["commitmentValid"][playerId] = self.verifyPlayerCommitment(playerId)
            
        return results

def verifyPokerGame(gameDataFile: str):
    print("🔍 Starting MiacatPoker verification...")
    
    with open(gameDataFile, 'r') as f:
        gameData = json.load(f)
    
    playerResponse = input("\nWere you a player in this game? (Y/N): ").upper()
    
    if playerResponse == 'Y':
        playerName = input("Enter your player name, case sensitive: ")
        if playerName in gameData['clientSeeds']:
            playerSeed = input("Enter your client seed to verify: ")
            storedSeed = gameData['clientSeeds'][playerName]['seed']
            
            if playerSeed == storedSeed:
                print(f"\n✨ Player Verification Success!")
                print(f"Your position was: {gameData['positions'][playerName]}")
                print(f"Your salt was: {gameData['clientSeeds'][playerName]['salt']}")
                print(f"Your commitment was: {gameData['commitments'][playerName]}")
            else:
                print("\n❌ Client seed doesn't match stored value!")
                print("This could indicate game tampering if you did not generate or try to edit the game data record yourself!")
                print("Please make sure you entered your correct client seed, and that there are no trailing or leading spaces or incorrect upper or lowercasing, and that the game data json file is unchanged, including the version number, which must be the same.")
                return False
        else:
            print("\n❌ Player name not found in game data! Your name is case-sensitive as it was entered into the game originally.")
            return False
    
    verifier = MiacatVerifier(gameData)
    results = verifier.verifyGame()
    
    print("\n✨ Verification Results:")
    print(f"Server Hash Valid: {'✅' if results['serverHashValid'] else '❌'}")
    print(f"Double Hash Valid: {'✅' if results['doubleHashValid'] else '❌'}")
    print(f"Game/Verifier Versions Compatible: {'✅' if results['checkVersionValid'] else '❌'}")

    
    print("\n👥 Player Commitments:")
    for player, valid in results["commitmentValid"].items():
        print(f"{player}: {'✅' if valid else '❌'}")
    
    print(f"\nDeck Generation Valid: {'✅' if results['deckValid'] else '❌'}")
    
    allValid = (results['serverHashValid'] and 
                results['doubleHashValid'] and
                results['checkVersionValid'] and
                results['deckValid'] and 
                all(results["commitmentValid"].values()))
       
    print(f"\n🏁 Overall Verification: {'✅ Valid' if allValid else '❌ Invalid'}")
    
    return results

if __name__ == "__main__":
    try:
        verifyPokerGame("game_data.json")
    except FileNotFoundError:
        print("❌ Game data file not found! Please ensure 'game_data.json' exists!")
    except json.JSONDecodeError:
        print("❌ Invalid game data format!")
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
