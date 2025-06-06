from decimal import Decimal
from django.contrib.gis.geos import Point as DjangoGEOSPoint
from django.db import transaction
from webcam.models import IntersectionModel, IntersectionEntryModel
from webcam.utils import logger_background  # Assuming you have a logger configured

class IntersectionEntry:
    def __init__(self, intersection_entry_id, entry_number, coordinates1_tuple, coordinates2_tuple, traffic_score):
        self.id = intersection_entry_id # This would be the CharField primary key
        self.entry_number = entry_number
        # Store coordinates as tuples (lon, lat) for easier JSON handling
        self.coordinates1_tuple = coordinates1_tuple # (lon, lat)
        self.coordinates2_tuple = coordinates2_tuple # (lon, lat)
        self.traffic_score = traffic_score

    def to_json(self):
        return {
            "id": self.id,
            "entry_number": self.entry_number,
            "coordinates1": list(self.coordinates1_tuple), # Convert tuple to list for JSON
            "coordinates2": list(self.coordinates2_tuple), # Convert tuple to list for JSON
            "traffic_score": self.traffic_score
        }

    @classmethod
    def from_json(cls, data, entry_id_prefix="entry"):
        # Expects coordinates as [lon, lat] or (lon, lat)
        coords1 = data.get("coordinates1")
        coords2 = data.get("coordinates2")
        if not isinstance(coords1, (list, tuple)) or len(coords1) != 2:
            raise ValueError("Invalid format for coordinates1")
        if not isinstance(coords2, (list, tuple)) or len(coords2) != 2:
            raise ValueError("Invalid format for coordinates2")

        entry_number = data.get("entry_number")
        # Construct a default ID if not provided, or expect it in data
        entry_id = data.get("id", f"{entry_id_prefix}{entry_number}")

        return cls(
            intersection_entry_id=entry_id,
            entry_number=entry_number,
            coordinates1_tuple=tuple(coords1),
            coordinates2_tuple=tuple(coords2),
            traffic_score=data.get("traffic_score")
        )

class Intersection:
    def __init__(self, intersection_id, name, address, country, city, coordxy_tuple,
                 entries_number, individual_toggle, is_smart_algorithm_enabled, entries=None):
        self.id = intersection_id # This is the CharField primary key
        self.name = name
        self.address = address
        self.country = country
        self.city = city
        self.coordXY = DjangoGEOSPoint(x=Decimal(coordxy_tuple[0]), y=Decimal(coordxy_tuple[1]), srid=4326) # Store as (lon, lat) tuple
        self.entriesNumber = entries_number
        self.individualToggle = individual_toggle
        self.is_smart_algorithm_enabled = is_smart_algorithm_enabled
        self.entries = entries if entries is not None else [] # List of IntersectionEntry objects

    @classmethod
    def _parse_point_data(cls, point_data):
        """Helper to parse point data into (lon, lat) tuple."""
        if isinstance(point_data, (list, tuple)) and len(point_data) == 2:
            # Assuming [lon, lat] or (lon, lat)
            return float(point_data[0]), float(point_data[1])
        elif isinstance(point_data, dict) and point_data.get("type") == "Point" and "coordinates" in point_data:
            # GeoJSON dict
            coords = point_data["coordinates"]
            if isinstance(coords, (list, tuple)) and len(coords) == 2:
                return float(coords[0]), float(coords[1])
        # Add more parsing logic if needed, e.g., for Decimal objects if they come directly
        raise ValueError(f"Unsupported point data format: {point_data}")


    @classmethod
    def from_json(cls, data):
        coordXY_data = data.get("coordXY")
        if not coordXY_data:
            raise ValueError("coordXY is required.")
        coordXY_tuple = cls._parse_point_data(coordXY_data)

        entries_data = data.get("entries", [])
        parsed_entries = []
        intersection_id = data.get("id") # Get intersection ID for prefixing entry IDs

        for i, entry_json in enumerate(entries_data):
            # Ensure entry_json has 'entry_number' or set it by order
            if "entry_number" not in entry_json:
                entry_json["entry_number"] = i
            # Pass a prefix for default entry ID generation if entry ID is not in entry_json
            entry_id_prefix = f"{intersection_id}_entry" if intersection_id else f"unknown_intersection_entry"
            parsed_entries.append(IntersectionEntry.from_json(entry_json, entry_id_prefix=entry_id_prefix))

        return cls(
            intersection_id=data.get("id"),
            name=data.get("name"),
            address=data.get("address"),
            country=data.get("country"),
            city=data.get("city"),
            coordxy_tuple=coordXY_tuple,
            entries_number=data.get("entriesNumber", len(parsed_entries)), # Default to length of parsed entries
            individual_toggle=data.get("individualToggle", False),
            is_smart_algorithm_enabled=data.get("is_smart_algorithm_enabled", True),
            entries=parsed_entries
        )

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "country": self.country,
            "city": self.city,
            "coordXY": self.coordXY.json, # Convert tuple to list for JSON
            "entriesNumber": self.entriesNumber,
            "individualToggle": self.individualToggle,
            "is_smart_algorithm_enabled": self.is_smart_algorithm_enabled,
            "entries": [entry.to_json() for entry in self.entries]
        }

    @transaction.atomic
    def save_to_db(self):
        if not self.id:
            raise ValueError("Intersection ID is required to save to database.")

        # Prepare data for IntersectionModel, using the 'name' attribute from models.py
        intersection_model_data = {
            "Id": self.id, # Django model field name is "ID"
            "IntersectionName": self.name,
            "IntersectionAddress": self.address,
            "IntersectionCountry": self.country,
            "IntersectionCity": self.city,
            "coordXY": self.coordXY, # lon, lat
            "entriesNumber": self.entriesNumber,
            "individualToggle": self.individualToggle,
            "IntersectionIsSmartAlgorithmEnabled": self.is_smart_algorithm_enabled
        }

        # Use update_or_create to handle both new and existing intersections
        intersection_instance, created = IntersectionModel.objects.update_or_create(
            Id=self.id, # Query by the primary key
            defaults=intersection_model_data
        )
        if created:
            logger_background.info(f"Created IntersectionModel with ID: {self.id}")
        else:
            logger_background.info(f"Updated IntersectionModel with ID: {self.id}")
            # If updating, you might want to clear existing entries and re-add them
            # or implement more sophisticated entry update logic.
            # For simplicity, this example clears and re-adds.
            intersection_instance.entries.all().delete()


        for entry_obj in self.entries:
            if not entry_obj.id:
                raise ValueError(f"ID is required for entry number {entry_obj.entry_number}")
            IntersectionEntryModel.objects.create(
                Id=entry_obj.id, # Django model field name is "id"
                intersectionId=intersection_instance,
                entry_number=entry_obj.entry_number,
                coordinates1=DjangoGEOSPoint(entry_obj.coordinates1_tuple[0], entry_obj.coordinates1_tuple[1], srid=4326),
                coordinates2=DjangoGEOSPoint(entry_obj.coordinates2_tuple[0], entry_obj.coordinates2_tuple[1], srid=4326),
                traffic_score=entry_obj.traffic_score
            )
        logger_background.info(f"Saved/Updated {len(self.entries)} entries for intersection ID: {self.id}")
        return intersection_instance # Return the Django model instance

    @classmethod
    @transaction.atomic
    def delete_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(Id=intersection_id)
            # Related entries will be deleted due to on_delete=models.CASCADE
            intersection_instance.delete()
            logger_background.info(f"Deleted IntersectionModel and its entries with ID: {intersection_id}")
            return True
        except IntersectionModel.DoesNotExist:
            logger_background.warning(f"IntersectionModel with ID: {intersection_id} not found for deletion.")
            return False
        except Exception as e:
            logger_background.error(f"Error deleting intersection ID {intersection_id}: {e}", exc_info=True)
            return False

    @classmethod
    def load_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            entries_queryset = intersection_instance.entries.all().order_by('entry_number')

            loaded_entries = []
            for entry_model in entries_queryset:
                loaded_entries.append(IntersectionEntry(
                    intersection_entry_id=entry_model.id,
                    entry_number=entry_model.entry_number,
                    coordinates1_tuple=(entry_model.coordinates1.x, entry_model.coordinates1.y), # lon, lat
                    coordinates2_tuple=(entry_model.coordinates2.x, entry_model.coordinates2.y), # lon, lat
                    traffic_score=entry_model.traffic_score
                ))

            return cls(
                intersection_id=intersection_instance.id,
                name=intersection_instance.name,
                address=intersection_instance.address,
                country=intersection_instance.country,
                city=intersection_instance.city,
                coordxy_tuple=(intersection_instance.coordXY.x, intersection_instance.coordXY.y), # lon, lat
                entries_number=intersection_instance.entriesNumber,
                individual_toggle=intersection_instance.individualToggle,
                is_smart_algorithm_enabled=intersection_instance.enabled_smart_algorithm,
                entries=loaded_entries
            )
        except IntersectionModel.DoesNotExist:
            logger_background.warning(f"IntersectionModel with ID: {intersection_id} not found in DB.")
            return None
        except Exception as e:
            logger_background.error(f"Error loading intersection ID {intersection_id} from DB: {e}", exc_info=True)
            return None