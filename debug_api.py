import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

def testar_conexao():
    url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
    params = {"id": "71"} # Brasileirão
    
    print(f"Testando chave: {API_KEY[:5]}...{API_KEY[-5:]}")
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("API funcionando para o endpoint /leagues!")
            print(f"Ligas encontradas: {len(response.json().get('response', []))}")
        else:
            print(f"Erro: {response.text}")
    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    testar_conexao()
