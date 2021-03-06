import firebase_admin
import os
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date


class FireBaseContainer:
    def __init__(self):
        self.credentials = {
            "type": "service_account",
            "project_id": "bootleg-rhythm",
            "private_key_id": os.environ.get("private_key_id"),
            "private_key": "\n".join(os.environ.get("private_key").split("\\n")),
            "client_email": "firebase-adminsdk-88ew4@bootleg-rhythm.iam.gserviceaccount.com",
            "client_id": "111309818007103686425",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-88ew4%40bootleg-rhythm.iam.gserviceaccount.com"
        }
        self.cred = credentials.Certificate(self.credentials)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

    def add_new_server(self, guild_id):
        settings_collection = self.db.collection("settings")
        default_settings = settings_collection.document(
            "default_settings").get().to_dict()

        settings_collection.document(guild_id).set(default_settings)

    def remove_server(self, guild_id):
        settings_collection = self.db.collection("settings")
        settings_collection.document(guild_id).delete()

    def update_prefix(self, guild_id, prefix):
        settings = self.db.collection("settings").document(
            guild_id).get().to_dict()

        settings["prefix"] = prefix

        self.db.collection("settings").document(guild_id).set(settings)

    def update_announce_songs_settings(self, guild_id, announce_song):
        settings = self.db.collection("settings").document(
            guild_id).get().to_dict()

        settings["announcesongs"] = announce_song

        self.db.collection("settings").document(guild_id).set(settings)

    def add_text_channel_to_blacklist(self, guild_id, text_channel):
        settings = self.db.collection("settings").document(
            guild_id).get().to_dict()

        if text_channel in settings["blacklist"]:
            return

        settings["blacklist"].append(text_channel)

        self.db.collection("settings").document(guild_id).set(settings)

    def is_in_blacklist(self, guild_id, text_channel_id):
        black_list = set(self.db.collection("settings").document(
            guild_id).get().to_dict()["blacklist"])

        if text_channel_id in black_list:
            return True
        else:
            return False

    def retrieve_prefix(self, guild_id):
        settings_collection = self.db.collection("settings")
        guild_settings = settings_collection.document(
            guild_id).get().to_dict()

        return guild_settings["prefix"]

    def retrieve_announce_songs_settings(self, guild_id):
        settings_collection = self.db.collection("settings")
        guild_settings = settings_collection.document(
            guild_id).get().to_dict()

        return guild_settings["announcesongs"]
