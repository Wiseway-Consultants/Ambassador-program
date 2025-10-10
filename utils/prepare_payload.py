

class ProspectPreparePayload:

    @staticmethod
    def ghl_contact_create(data):
        return {
            "firstName": data.get("first_name", ""),
            "lastName": data.get("last_name", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
            "companyName": data.get("restaurant_organisation_name", ""),
            "country": data.get("country", ""),
            "tags": ["ambassador prospect"]
        }

    @staticmethod
    def ghl_opportunity_create(data, contact_id):
        return {
            "name": f"{data.get('email')} {data.get('restaurant_organisation_name')}",
            "status": "open",
            "contactId": contact_id
        }


prospect_prepare_payload = ProspectPreparePayload()
