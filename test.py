# scrape.py
import json
import os
import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional

import requests
from pyproj import Transformer
from shapely.geometry import box

from enums import ProjectionSystem, BoundingBoxCoords, AttributeKeys
from exceptions import BoundingBoxError, DataFetchError, DataProcessingError
from logging_config import setup_logging
from load_config import load_config

class NYBridgeScraper:
    def __init__(self, state_name: str) -> None:

        #setup_logging(log_file_path=self.config['LOG_FILE_PATH'])
        setup_logging()
        self.logger = logging.getLogger('NYBridgeScraper')
        
        self.state_name=state_name
        self.config = load_config(state_name)

        self.api_url = self.config['API_URL']
        self.overpass_turbo_url = self.config['OVERPASS_TURBO_URL']
        self.headers = self.config['OVERPASS_TURBO_HEADERS']
        self.completed_response_path = os.path.join(os.getcwd(), *self.config['COMPLETED_RESPONSES_PATH'].split('/'))
        self.failed_response_path = os.path.join(os.getcwd(), *self.config['FAILED_REQUESTS_PATH'].split('/'))
        self.all_scraped_data_path = os.path.join(os.getcwd(), *self.config['ALL_SCRAPED_DATA_PATH'].split('/'))
        self.side_length_m = self.config['SIDE_LENGTH_KM']*1000
        self.max_retries = self.config['MAX_RETRIES']
        self.max_workers = self.config['MAX_WORKERS']
        self.api_url_params=self.config['API_URL_PARAMS']
    

    def get_bounding_box(self, region: str) -> Tuple[List[str], List[str]]:
        """
        Fetch the bounding box for a given region using OpenStreetMap Nominatim API.

        Args:
            region (str): The name of the region to fetch the bounding box for.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing the API response and the bounding box.

        Raises:
            BoundingBoxError: If there's an error fetching the bounding box.
        """
        self.logger.info(f"Fetching bounding box for region: {region}")

        try:
            response = requests.get(self.overpass_turbo_url, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.logger.info(f"Successfully fetched bounding box for {region}")
            return data, data[0]["boundingbox"]
        except requests.RequestException as e:
            self.logger.error(f"Error fetching bounding box for {region}: {str(e)}", exc_info=True)
            raise BoundingBoxError(f"Error fetching bounding box for {region}: {str(e)}") from e

    def generate_grid_boxes(self, bbox: List[str]) -> List[Dict]:
        """
        Generate grid boxes for the given bounding box.

        Args:
            bbox (List[str]): The bounding box coordinates.

        Returns:
            List[Dict]: A list of grid boxes.
        """
        self.logger.info(f"Generating grid boxes for bounding box: {bbox}")

        ny_lat_min, ny_lat_max = float(bbox[0]), float(bbox[1])
        ny_lon_min, ny_lon_max = float(bbox[2]), float(bbox[3])

        # Create a Transformer object
        transformer = Transformer.from_proj(ProjectionSystem.WGS84.value, ProjectionSystem.UTM18N.value)

        # Transform the coordinates
        ny_xmin, ny_ymin = transformer.transform(ny_lon_min, ny_lat_min)
        ny_xmax, ny_ymax = transformer.transform(ny_lon_max, ny_lat_max)


        grid_boxes = []
        current_x = ny_xmin
        while current_x < ny_xmax:
            current_y = ny_ymin
            while current_y < ny_ymax:
                box_coords = box(current_x, current_y, current_x + self.side_length_m, current_y + self.side_length_m)
                grid_boxes.append({
                    BoundingBoxCoords.XMIN.value: box_coords.bounds[0],
                    BoundingBoxCoords.YMIN.value: box_coords.bounds[1],
                    BoundingBoxCoords.XMAX.value: box_coords.bounds[2],
                    BoundingBoxCoords.YMAX.value: box_coords.bounds[3],
                    "spatialReference": {"wkid": 26918, "latestWkid": 26918}
                })
                current_y += self.side_length_m
            current_x += self.side_length_m

        self.logger.info(f"Generated {len(grid_boxes)} grid boxes")
        return grid_boxes

    def load_previous_state(self) -> Tuple[List, List]:
        """
        Load the previous state from files.

        Returns:
            Tuple[List, List]: A tuple containing completed responses and failed requests.
        """
        completed_responses = []
        failed_requests = []

        if os.path.exists(self.completed_response_path):
            with open(self.completed_response_path, 'r') as f:
                completed_responses = json.load(f)
            self.logger.info(f"Loaded {len(completed_responses)} completed responses from file")
        else:
            self.logger.info("No previous completed responses file found")

        if os.path.exists(self.failed_response_path):
            with open(self.failed_response_path, 'r') as f:
                failed_requests = json.load(f)
            self.logger.info(f"Loaded {len(failed_requests)} failed requests from file")
        else:
            self.logger.info("No previous failed requests file found")

        return completed_responses, failed_requests

    def fetch_data(self, box: Dict) -> Optional[List]:
        """
        Fetch data for a given grid box from the API.

        Args:
            box (Dict): The grid box coordinates.

        Returns:
            Optional[List]: The fetched data or None if the request failed.

        Raises:
            DataFetchError: If there's an error fetching data from the API.
        """
        self.api_url_params["geometry"]= json.dumps(box)

        try:
            response = self.retry_with_backoff(requests.get, self.api_url, params=self.api_url_params, timeout=5, max_retries=self.max_retries)
            json_response = response.json()
            
            if 'features' not in json_response:
                raise DataFetchError(f"API response format unexpected for box {box}")
            
            features = json_response['features']
            # self.logger.info(f"Successfully fetched {len(features)} features for box {box[BoundingBoxCoords.XMIN.value]},{box[BoundingBoxCoords.YMIN.value]},{box[BoundingBoxCoords.XMAX.value]},{box[BoundingBoxCoords.YMAX.value]}")
            return features
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error fetching data for box {box[BoundingBoxCoords.XMIN.value]},{box[BoundingBoxCoords.YMIN.value]},{box[BoundingBoxCoords.XMAX.value]},{box[BoundingBoxCoords.YMAX.value]}: {str(e)}", exc_info=True)
            raise DataFetchError(f"Error fetching data for box {box}") from e

    def process_grid_boxes(self, grid_boxes: List[Dict], completed_responses: List) -> Tuple[List, List]:
        """
        Process grid boxes and fetch data concurrently.

        Args:
            grid_boxes (List[Dict]): The list of grid boxes to process.
            completed_responses (List): The list of previously completed responses.

        Returns:
            Tuple[List, List]: A tuple containing the results and failed requests.

        Raises:
            ProcessingError: If there's an error during the processing of grid boxes.
        """
        try:
            grid_boxes_to_process = self._filter_unprocessed_boxes(grid_boxes, completed_responses)
            total_boxes = len(grid_boxes_to_process)
            self.logger.info(f"Processing {total_boxes} new grid boxes")
            print(f"Total bounding boxes to process: {total_boxes}")

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_box = self._create_futures(executor, grid_boxes_to_process)
                return self._process_futures(future_to_box, total_boxes)
        except Exception as e:
            self.logger.error(f"Error occurred while processing grid boxes: {str(e)}", exc_info=True)
            raise DataProcessingError(f"Failed to process grid boxes: {str(e)}") from e

    def _filter_unprocessed_boxes(self, grid_boxes: List[Dict], completed_responses: List) -> List[Dict]:
        """
        Filter out already processed grid boxes from the list.

        Parameters:
            grid_boxes (List[Dict]): The list of grid boxes to be processed.
            completed_responses (List): The list of previously completed responses.

        Returns:
            List[Dict]: The list of grid boxes that have not yet been processed.
        """
        try:
            completed_boxes = {(box[BoundingBoxCoords.XMIN.value], box[BoundingBoxCoords.YMIN.value], 
                                box[BoundingBoxCoords.XMAX.value], box[BoundingBoxCoords.YMAX.value]) 
                               for box, _, _ in completed_responses}
            return [box for box in grid_boxes if (box[BoundingBoxCoords.XMIN.value], box[BoundingBoxCoords.YMIN.value], 
                                                  box[BoundingBoxCoords.XMAX.value], box[BoundingBoxCoords.YMAX.value]) not in completed_boxes]
        except KeyError as e:
            self.logger.error(f"Invalid box format encountered: {str(e)}", exc_info=True)
            raise ValueError(f"Invalid box format: {str(e)}") from e

    def _create_futures(self, executor: ThreadPoolExecutor, grid_boxes: List[Dict]) -> Dict:
        """
        Create futures for each grid box to process them concurrently.

        Parameters:
            executor (ThreadPoolExecutor): The executor to submit futures to.
            grid_boxes (List[Dict]): The list of grid boxes to process.

        Returns:
            Dict: A dictionary mapping futures to their corresponding grid boxes.
        """

        return {executor.submit(self.fetch_data, box): box for box in grid_boxes}

    def _process_futures(self, future_to_box: Dict, total_boxes: int) -> Tuple[List, List]:
        """
        Process futures and collect results, handling successful and failed fetches.

        Parameters:
            future_to_box (Dict): A dictionary mapping futures to their corresponding grid boxes.
            total_boxes (int): The total number of boxes being processed.

        Returns:
            Tuple[List, List]: A tuple containing the results and failed requests.
        """
        results = []
        failed = []
        for i, future in enumerate(as_completed(future_to_box), 1):
            box = future_to_box[future]
            try:
                data = future.result()
                results, failed =self._handle_future_result(data, box, results, failed, i, total_boxes)
            except DataFetchError as exc:
                failed=self._handle_future_exception(exc, box, failed, i, total_boxes)
            except Exception as e:
                self.logger.error(f"Unexpected error processing future for box {box}: {str(e)}", exc_info=True)
                failed.append(box)
            self._apply_rate_limiting(i)
        self.logger.info(f"Completed processing. {len(results)} boxes succeeded, {len(failed)} boxes failed")
        return results, failed

    def _handle_future_result(self, data: Optional[List], box: Dict, results: List, failed: List, i: int, total_boxes: int) -> None:
        """
        Handle the result of a future by adding data to the results list or logging failure.

        Parameters:
            data (Optional[List]): The data returned from the future.
            box (Dict): The bounding box being processed.
            results (List): The list to append successful results to.
            failed (List): The list to append failed boxes to.
            i (int): The current index of the box being processed.
            total_boxes (int): The total number of boxes being processed.

        Returns:
            Tuple[List, List]: Updated results and failed lists.
        """
        try:
            if data is not None:
                results.append((box, data, {AttributeKeys.total_features_in_box.value: len(data)}))
                print(f"{i}/{total_boxes} Box {box} has {len(data)} features")
            else:
                failed.append(box)
                print(f"{i}/{total_boxes} Failed to fetch data for box {box}")
                self.logger.warning(f"Failed to fetch data for box {box[BoundingBoxCoords.XMIN.value]},{box[BoundingBoxCoords.YMIN.value]},"
                                    f"{box[BoundingBoxCoords.XMAX.value]},{box[BoundingBoxCoords.YMAX.value]}")
        except Exception as e:
            self.logger.error(f"Error handling future result for box {box}: {str(e)}", exc_info=True)
            failed.append(box)
        return results, failed
            
    def _handle_future_exception(self, exc: Exception, box: Dict, failed: List, i: int, total_boxes: int) -> None:
        """
        Handle exceptions raised during future execution by logging and updating the failed list.

        Parameters:
            exc (Exception): The exception raised during future execution.
            box (Dict): The bounding box that generated the exception.
            failed (List): The list to append failed boxes to.
            i (int): The current index of the box being processed.
            total_boxes (int): The total number of boxes being processed.

        Returns:
            List: Updated failed list.
        """
        try:
            self.logger.error(f"Box {box[BoundingBoxCoords.XMIN.value]},{box[BoundingBoxCoords.YMIN.value]},"
                            f"{box[BoundingBoxCoords.XMAX.value]},{box[BoundingBoxCoords.YMAX.value]} generated an exception: {exc}", 
                            exc_info=True)
            failed.append(box)
            print(f"{i}/{total_boxes} Error processing box {box}: {exc}")
        except Exception as e:
            self.logger.error(f"Error handling exception for box {box}: {str(e)}", exc_info=True)
            failed.append(box)
        return failed

    def _apply_rate_limiting(self, i: int) -> None:
        """
        Apply rate limiting to prevent overwhelming the API by sleeping periodically.

        Parameters:
            i (int): The current index of the box being processed.
        """
        if i % 5 == 0:
            time.sleep(1)

    def save_results(self, completed_responses: List, failed_requests: List) -> None:
        """
        Save the completed responses and failed requests to files.

        Args:
            completed_responses (List): The list of completed responses.
            failed_requests (List): The list of failed requests.
        """
        
        with open(self.completed_response_path, 'w') as f:
            json.dump(completed_responses, f, indent=4)
        self.logger.info(f"Saved {len(completed_responses)} completed responses to {self.completed_response_path}")

        with open(self.failed_response_path, 'w') as f:
            json.dump(failed_requests, f, indent=4)
        self.logger.info(f"Saved {len(failed_requests)} failed requests to {self.failed_response_path}")

    @staticmethod
    def retry_with_backoff(func, *args, max_retries: int, **kwargs):
        """
        Retry a function with exponential backoff.

        Args:
            func: The function to retry.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: If all retries fail.
        """
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.warning(f"Retrying due to {type(e).__name__}. Attempt {attempt + 1}/{max_retries}. Waiting for {wait_time:.2f} seconds.")
                time.sleep(wait_time)
            except (requests.HTTPError, requests.RequestException) as e:
                # For these exceptions, we don't retry
                logging.error(f"Non-retryable error occurred: {type(e).__name__}: {str(e)}")
                raise

    def scrape(self):
        self.logger.info("Starting New York State Data Fetcher")

        try:
            response, bbox = self.get_bounding_box(self.state_name)
            self.logger.info(f"Bounding box for New York State: {bbox}")

            grid_boxes = self.generate_grid_boxes(bbox)
            completed_responses, failed_requests = self.load_previous_state()

            results, failed = self.process_grid_boxes(grid_boxes, completed_responses)

            completed_responses.extend(results)
            failed_requests=failed

            self.save_results(completed_responses, failed_requests)

            total_features = sum(len(data) for _, data, _ in results)
            self.logger.info(f"Retrieved data for {len(results)} boxes, {len(failed)} boxes failed and got {total_features} features")
            print(f"Retrieved data for {len(results)} boxes, {len(failed)} boxes failed and got {total_features} features")

        except (BoundingBoxError, DataFetchError) as e:
            self.logger.error(f"An error occurred: {str(e)}", exc_info=True)
            print(f"An error occurred: {str(e)}")

        self.logger.info("New York State Data Fetcher completed")
        print("New York State Data Fetcher completed")

def main():
    state_name = "New York State"
    scraper = NYBridgeScraper(state_name=state_name)
    scraper.scrape()

if __name__ == "__main__":
    main()