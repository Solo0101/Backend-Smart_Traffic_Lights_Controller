import abc
import datetime
import json
import uuid
from abc import ABC

from django.contrib.gis.geos import Point as DjangoGEOSPoint, GEOSException
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from webcam.models import IntersectionModel, IntersectionEntryModel, AvgVehicleThroughputDataPointModel, \
    AvgWaitingTimeDataPointModel
from webcam.utils import logger_main

def _convert_json_to_point(data) -> DjangoGEOSPoint | None:
    """
    Robustly converts various JSON/dict formats to a Django GEOS Point object.
    Returns a Point object or None if conversion fails.
    """
    # If data is a raw JSON string, parse it into a Python dict first
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print("Error: Invalid JSON string provided.")
            return None

    if not isinstance(data, dict):
        print("Error: Input data must be a dictionary or a valid JSON string.")
        return None

    try:
        # Case 1: Standard GeoJSON format
        if 'type' in data and data.get('type') == 'Point' and 'coordinates' in data:
            point = GEOSGeometry(json.dumps(data), srid=4326)
            return point

        # Case 2: Simple { "longitude": ..., "latitude": ... } format
        elif 'longitude' in data and 'latitude' in data:
            point = DjangoGEOSPoint(
                x=float(data['longitude']),
                y=float(data['latitude']),
                srid=4326
            )
            return point

        else:
            print("Error: JSON object does not match known formats (GeoJSON or {lon/lat}).")
            return None

    except (GEOSException, TypeError, ValueError, KeyError) as e:
        print(f"An error occurred during conversion: {e}")
        return None

class DataPoint(ABC):
    def __init__(self, intersection_id, timestamp, value):
        self.intersection_id = intersection_id
        self.timestamp = timestamp
        self.value = value

    def to_json(self):
        return {
            "timestamp": self.timestamp,
            "value": self.value
        }

    @transaction.atomic
    @abc.abstractmethod
    def save_to_db(self):
        raise NotImplementedError("Please Implement this method")

    @classmethod
    @abc.abstractmethod
    def load_from_db(cls, intersection_id):
        raise NotImplementedError("Please Implement this method")


class AvgWaitingTimeDataPoint(DataPoint):
    @transaction.atomic
    def save_to_db(self):
        AvgWaitingTimeDataPointModel.objects.create(
            id=str(uuid.uuid4()),
            intersection_id=self.intersection_id,
            timestamp=datetime.datetime.now(),
            value=self.value
        )

    @classmethod
    def load_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            loaded_data_points = AvgWaitingTimeDataPointModel.objects.filter(intersection_id=intersection_instance.id)
            loaded_data_points_list = []
            for loaded_data_point in loaded_data_points:
                loaded_data_points_list.append(cls(
                    intersection_id=loaded_data_point.intersection_id,
                    timestamp=loaded_data_point.timestamp,
                    value=loaded_data_point.value
                ))

            loaded_data_points_list.sort(key=lambda data_point: data_point.timestamp, reverse=True)
            return loaded_data_points_list
        except Exception as e:
            logger_main.error(f"Error loading AvgWaitingTimeDataPoint list for intersection ID {intersection_id} from DB: {e}", exc_info=True)
            return None

class AvgVehicleThroughputDataPoint(DataPoint):
    @transaction.atomic
    def save_to_db(self):
        AvgVehicleThroughputDataPointModel.objects.create(
            id=str(uuid.uuid4()),
            intersection_id=self.intersection_id,
            timestamp=datetime.datetime.now(),
            value=self.value
        )

    @classmethod
    def load_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            loaded_data_points = AvgVehicleThroughputDataPointModel.objects.filter(intersection_id=intersection_instance.id)
            loaded_data_points_list = []
            for loaded_data_point in loaded_data_points:
                loaded_data_points_list.append(cls(
                    intersection_id=loaded_data_point.intersection_id,
                    timestamp=loaded_data_point.timestamp,
                    value=loaded_data_point.value
                ))

            loaded_data_points_list.sort(key=lambda data_point: data_point.timestamp, reverse=True)
            return loaded_data_points_list
        except Exception as e:
            logger_main.error(f"Error loading AvgVehicleThroughputDataPoint list for intersection ID {intersection_id} from DB: {e}", exc_info=True)
            return None



class IntersectionEntry:
    def __init__(self, entry_id, entry_number, traffic_score, coordinates1=DjangoGEOSPoint(), coordinates2=DjangoGEOSPoint()):
        self.id = entry_id
        self.entry_number = entry_number
        self.coordinates1 = coordinates1
        self.coordinates2 = coordinates2
        self.traffic_score = traffic_score

    def to_json(self):
        return {
            "id": self.id,
            "entryNumber": self.entry_number,
            "coordinates1": None if self.coordinates1 is None else self.coordinates1.json, # Convert DjangoGEOSPoint to JSON
            "coordinates2": None if self.coordinates2 is None else self.coordinates2.json, # Convert DjangoGEOSPoint to JSON
            "trafficScore": self.traffic_score
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            entry_id=data.get("id"),
            entry_number=data.get("entryNumber"),
            coordinates1=_convert_json_to_point(data.get("coordinates1")),
            coordinates2=_convert_json_to_point(data.get("coordinates2")),
            traffic_score=data.get("trafficScore")
        )

    @classmethod
    def load_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            loaded_entries = IntersectionEntryModel.objects.filter(intersection_id=intersection_instance.id)
            entries_list = []
            for loaded_entry in loaded_entries:
                entries_list.append(cls(
                    entry_id=loaded_entry.id,
                    entry_number=loaded_entry.entry_number,
                    coordinates1=loaded_entry.coordinates1,
                    coordinates2=loaded_entry.coordinates2,
                    traffic_score=loaded_entry.traffic_score
                ))
            return entries_list
        except Exception as e:
            logger_main.error(f"Error loading entries list for intersection ID {intersection_id} from DB: {e}", exc_info=True)
            return None

class Intersection:
    def __init__(self, intersection_id, name, address, country, city, coordxy,
                 entries_number, individual_toggle, smart_algorithm_enabled, entries):
        self.id = intersection_id
        self.name = name
        self.address = address
        self.country = country
        self.city = city
        self.coordXY = coordxy # Store as (lon, lat) tuple
        self.entriesNumber = entries_number
        self.individualToggle = individual_toggle
        self.smartAlgorithmEnabled = smart_algorithm_enabled
        self.entries = entries
        self.avg_waiting_time_data_points = AvgWaitingTimeDataPoint.load_from_db(intersection_id)
        self.avg_vehicle_throughput_data_points = AvgVehicleThroughputDataPoint.load_from_db(intersection_id)

    @classmethod
    def from_json(cls, data):
        if data.get("individualToggle") == "false":
            individualToggle_data = False
        elif data.get("individualToggle") == "true":
            individualToggle_data = True
        else:
            raise ValueError("individualToggle must be 'true' or 'false'.")

        if data.get("smartAlgorithmEnabled") == "true":
            smartAlgorithmEnabled_data = True
        elif data.get("smartAlgorithmEnabled") == "false":
            smartAlgorithmEnabled_data = False
        else:
            raise ValueError("smartAlgorithmEnabled must be 'true' or 'false'.")

        entries = data.get("entries")
        parsed_entries = []

        if entries == {} or entries == [] or entries is None:
            parsed_entries = []
        else:
            for i in range(0, data.get("entriesNumber"), 1):
                parsed_entries.append(IntersectionEntry.from_json(entries[i]))

        return cls(
            intersection_id=data.get("id"),
            name=data.get("name"),
            address=data.get("address"),
            country=data.get("country"),
            city=data.get("city"),
            coordxy=_convert_json_to_point(data.get("coordXY")),
            entries_number=data.get("entriesNumber"),
            individual_toggle=individualToggle_data,
            smart_algorithm_enabled=smartAlgorithmEnabled_data,
            entries=parsed_entries
        )

    def to_json(self):
        self.avg_waiting_time_data_points.sort(key=lambda data_point: data_point.timestamp)
        self.avg_vehicle_throughput_data_points.sort(key=lambda data_point: data_point.timestamp)
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "country": self.country,
            "city": self.city,
            "coordXY": self.coordXY.json, # Convert DjangoGEOSPoint to JSON
            "entriesNumber": self.entriesNumber,
            "individualToggle": self.individualToggle,
            "smartAlgorithmEnabled": self.smartAlgorithmEnabled,
            "entries": [entry.to_json() for entry in self.entries],
            "avgWaitingTimeDataPoints": [avg_waiting_time_data_point.to_json() for avg_waiting_time_data_point in self.avg_waiting_time_data_points],
            "avgVehicleThroughputDataPoints": [avg_vehicle_throughput_data_point.to_json() for avg_vehicle_throughput_data_point in self.avg_vehicle_throughput_data_points]
        }

    @transaction.atomic
    def save_to_db(self):
        if not self.id:
            self.id = str(uuid.uuid4())
            logger_main.info(f"Generated new ID for intersection: {self.id}")

        # Prepare data for IntersectionModel, using the 'name' attribute from models.py
        intersection_model_data = {
            "name": self.name,
            "address": self.address,
            "country": self.country,
            "city": self.city,
            "coordinates": self.coordXY,
            "entries_number": self.entriesNumber,
            "individual_toggle": self.individualToggle,
            "smart_algorithm_enabled": self.smartAlgorithmEnabled,
        }

        # Use update_or_create to handle both new and existing intersections
        intersection_instance, created = IntersectionModel.objects.update_or_create(
            id=self.id, # Query by the primary key
            defaults=intersection_model_data
        )

        if created:
            for entry_index in range(0, self.entriesNumber, 1):
                new_entry_id = str(uuid.uuid4())
                IntersectionEntryModel.objects.create(
                    id=new_entry_id,
                    intersection=intersection_instance,
                    entry_number=entry_index,
                    coordinates1=DjangoGEOSPoint(),
                    coordinates2=DjangoGEOSPoint(),
                    traffic_score=0
                )
            logger_main.info(f"Created IntersectionModel with ID: {self.id}")
        else:
            loaded_entries = IntersectionEntryModel.objects.filter(intersection_id=intersection_instance.id)
            for entry_model_instance in loaded_entries:
                entry_model_data = {
                    "entry_number": self.entries[entry_model_instance.entry_number].entry_number,
                    "coordinates1": self.entries[entry_model_instance.entry_number].coordinates1,
                    "coordinates2": self.entries[entry_model_instance.entry_number].coordinates2,
                    "traffic_score": self.entries[entry_model_instance.entry_number].traffic_score
                }

                IntersectionEntryModel.objects.update_or_create(
                    id=entry_model_instance.id,
                    defaults=entry_model_data
                )
            logger_main.info(f"Updated IntersectionModel with ID: {self.id}")

        logger_main.info(f"Saved/Updated {len(self.entries)} entries for intersection ID: {self.id}")
        return intersection_instance # Return the Django model instance

    @classmethod
    @transaction.atomic
    def delete_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            # Related entries will be deleted due to on_delete=models.CASCADE
            intersection_instance.delete()
            logger_main.info(f"Deleted IntersectionModel and its entries with ID: {intersection_id}")
            return True
        except IntersectionModel.DoesNotExist:
            logger_main.warning(f"IntersectionModel with ID: {intersection_id} not found for deletion.")
            return False
        except Exception as e:
            logger_main.error(f"Error deleting intersection ID {intersection_id}: {e}", exc_info=True)
            return False

    @classmethod
    def load_from_db(cls, intersection_id):
        try:
            intersection_instance = IntersectionModel.objects.get(id=intersection_id)
            loaded_entries = IntersectionEntry.load_from_db(intersection_id)

            return cls(
                intersection_id=intersection_instance.id,
                name=intersection_instance.name,
                address=intersection_instance.address,
                country=intersection_instance.country,
                city=intersection_instance.city,
                coordxy=intersection_instance.coordinates,
                entries_number=intersection_instance.entries_number,
                individual_toggle=intersection_instance.individual_toggle,
                smart_algorithm_enabled=intersection_instance.smart_algorithm_enabled,
                entries=loaded_entries
            )
        except IntersectionModel.DoesNotExist:
            logger_main.warning(f"IntersectionModel with ID: {intersection_id} not found in DB.")
            return None
        except Exception as e:
            logger_main.error(f"Error loading intersection ID {intersection_id} from DB: {e}", exc_info=True)
            return None