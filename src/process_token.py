import requests
import os


# URL của ứng dụng Flask
base_url = "http://127.0.0.1:3502"
token_file = "token.txt"


def get_saved_token():
    if os.path.exists(token_file):
        with open(token_file, "r") as file:
            token = file.read().strip()
        return token
    else:
        print(f"Token file {token_file} not found")
        return None


def access_profile():
    token = get_saved_token()
    print(token)
    if token:
        profile_url = f"{base_url}/profile"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(profile_url, headers=headers)
        if response.status_code == 200:
            profile_data = response.json()
            print(f"Profile data: {profile_data}")
            return profile_data
        else:
            print(f"Failed to access profile, status code: {response.status_code}")
    else:
        print("No token found")

# if __name__ == "__main__":
#     username = "user1"
#     password = "password1"
#
#     # Uncomment this line to login and save token
#     # login_and_save_token(username, password)
#
#     # Access profile using saved token
#     access_profile()
