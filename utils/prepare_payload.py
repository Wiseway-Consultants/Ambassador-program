

class ProspectPreparePayload:

    @staticmethod
    def ghl_contact_create(data, assign_to_user=None):
        payload = {
            "firstName": data.get("first_name", ""),
            "lastName": data.get("last_name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "companyName": data.get("restaurant_organisation_name", ""),
            "country": data.get("country", ""),
            "tags": ["ambassador prospect"]
        }
        if assign_to_user:
            payload["assignedTo"] = assign_to_user.get("ghl_user_id")
        return payload


prospect_prepare_payload = ProspectPreparePayload()
