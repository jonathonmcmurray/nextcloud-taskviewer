"""
Module for parsing and processing task data from Nextcloud.
"""
import logging


class TaskParser:
    """Handles parsing of task data from Nextcloud calendar objects."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_task_properties(self, task):
        """
        Extract summary, status, and due date from a task object using multiple methods.
        Returns tuple of (summary, status, due_date)
        """
        summary = "No Summary"
        status = "Unknown"
        due_date = ""  # Empty string instead of "None"

        # Different approach to extract task properties
        try:
            # Method 1: Use the task's built-in methods if available
            if hasattr(task, 'get_due') and callable(getattr(task, 'get_due')):
                due_val = task.get_due()
                if due_val:
                    # Handle vDDDTypes objects (date/datetime objects)
                    if hasattr(due_val, 'to_ical'):
                        due_date = due_val.to_ical().decode('utf-8') if isinstance(due_val.to_ical(), bytes) else str(due_val.to_ical())
                    else:
                        due_date = str(due_val)

            # Try to get properties using icalendar instance (which we know exists from debug)
            if hasattr(task, '_icalendar_instance') and task._icalendar_instance:
                # Get the VTODO component
                vtodo_component = task._icalendar_instance.walk('VTODO')[0] if task._icalendar_instance.subcomponents else None
                if vtodo_component:
                    # Extract summary
                    if hasattr(vtodo_component, 'get') and vtodo_component.get('SUMMARY'):
                        summary = str(vtodo_component.get('SUMMARY'))

                    # Extract status
                    if hasattr(vtodo_component, 'get') and vtodo_component.get('STATUS'):
                        status = str(vtodo_component.get('STATUS'))

                    # Extract due date (only DUE, not other date fields)
                    if hasattr(vtodo_component, 'get') and vtodo_component.get('DUE'):
                        due_val = vtodo_component.get('DUE')
                        # Handle vDDDTypes objects (date/datetime objects)
                        if hasattr(due_val, 'to_ical'):
                            due_date = due_val.to_ical().decode('utf-8') if isinstance(due_val.to_ical(), bytes) else str(due_val.to_ical())
                        else:
                            due_date = str(due_val)

            # Fallback: Use get_properties if icalendar_instance method didn't work
            if (summary == "No Summary" or status == "Unknown") and hasattr(task, 'get_properties'):
                props = task.get_properties(['SUMMARY', 'STATUS'])
                if 'SUMMARY' in props and summary == "No Summary":
                    summary = props['SUMMARY']
                if 'STATUS' in props and status == "Unknown":
                    status = props['STATUS']

            # Method 2: Parse raw ical data if methods didn't work well
            ical_data = getattr(task, 'data', None)
            if ical_data and (summary == "No Summary" or status == "Unknown" or due_date == "None"):
                ical_str = str(ical_data)

                # Only parse if we haven't gotten the values from methods
                if summary == "No Summary" and 'SUMMARY:' in ical_str:
                    start = ical_str.find('SUMMARY:') + len('SUMMARY:')
                    end = ical_str.find('\n', start)
                    if end == -1:  # If no newline, go to end of string
                        end = len(ical_str)
                    summary = ical_str[start:end].strip()

                if status == "Unknown" and 'STATUS:' in ical_str:
                    start = ical_str.find('STATUS:') + len('STATUS:')
                    end = ical_str.find('\n', start)
                    if end == -1:
                        end = len(ical_str)
                    status = ical_str[start:end].strip()

                # Only parse due date if we haven't gotten it from methods
                if due_date == "":
                    # Only look for DUE field, not other date fields
                    if 'DUE:' in ical_str:
                        start = ical_str.find('DUE:') + len('DUE:')
                        end = ical_str.find('\n', start)
                        if end == -1:
                            end = len(ical_str)
                        due_date = ical_str[start:end].strip()
                        # Remove VALUE parameter if present (e.g., DUE;VALUE=DATE:20260114)
                        if 'VALUE=' in due_date and ':' in due_date:
                            # Extract the date part after the colon
                            due_date = due_date.split(':', 1)[1]  # Split only on first colon
                    # Leave as "" if no DUE field is found
        except Exception as e:
            self.logger.error(f"Error parsing ical data: {e}", exc_info=True)

        return summary, status, due_date

    def extract_related_to(self, task):
        """
        Extract related-to information for parent-child relationships from a task object.
        Returns the related_to value or None if not found.
        """
        related_to = None
        # Look for RELATED-TO in the ical data (could be in various formats)
        ical_data = getattr(task, 'data', None)
        if ical_data:
            ical_str = str(ical_data)
            # Log the ical string to see what we're parsing
            self.logger.debug(f"ICAL DATA: {ical_str}")

            # Check for various formats of RELATED-TO
            if 'RELATED-TO:' in ical_str:
                self.logger.debug("FOUND RELATED-TO IN ICAL_STR")
            else:
                self.logger.debug("NO RELATED-TO FOUND IN ICAL_STR")
            # Find the RELATED-TO line regardless
            lines = ical_str.split('\n')
            for line in lines:
                if 'RELATED-TO:' in line:
                        self.logger.debug(f"FOUND RELATED-TO LINE: {line}")

                        # Handle formats like:
                        # RELATED-TO;RELTYPE=PARENT:uid
                        # RELATED-TO;RELTYPE=CHILD:uid
                        # RELATED-TO:uid
                        # RELATED-TO:[list of uids]

                        if 'RELTYPE=PARENT:' in line:
                            # Format: RELATED-TO;RELTYPE=PARENT:uid
                            parts = line.split('RELTYPE=PARENT:')
                            if len(parts) > 1:
                                related_to = parts[1].strip()
                                # Remove any trailing parameters after semicolon
                                if ';' in related_to:
                                    related_to = related_to.split(';')[0].strip()
                                self.logger.debug(f"EXTRACTED PARENT UID: {related_to}")
                                break
                        elif 'RELTYPE=CHILD:' in line:
                            # Format: RELATED-TO;RELTYPE=CHILD:uid
                            parts = line.split('RELTYPE=CHILD:')
                            if len(parts) > 1:
                                related_to = parts[1].strip()
                                # Remove any trailing parameters after semicolon
                                if ';' in related_to:
                                    related_to = related_to.split(';')[0].strip()
                                self.logger.debug(f"EXTRACTED CHILD UID: {related_to}")
                                break
                        else:
                            # Format: RELATED-TO:uid
                            if 'RELATED-TO:' in line and 'RELTYPE=' not in line:
                                related_part = line.split('RELATED-TO:')[1]
                                related_to = related_part.strip()
                                self.logger.debug(f"EXTRACTED GENERIC UID: {related_to}")
                                break
        
        return related_to