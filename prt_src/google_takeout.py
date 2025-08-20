"""
Google Takeout Contact Import

This module handles importing contacts from Google Takeout zip files,
including VCard parsing and profile image extraction.
"""

import zipfile
import vobject
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re


class GoogleTakeoutParser:
    """Parser for Google Takeout contact exports."""
    
    def __init__(self, zip_path: Path):
        """Initialize parser with path to Google Takeout zip file."""
        self.zip_path = zip_path
        self.contacts = []
        self.images = {}  # filename -> binary data mapping
        
    def validate_takeout_file(self) -> Tuple[bool, str]:
        """Validate that this is a Google Takeout file with contacts."""
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Look for Contacts directory and VCard files
                has_contacts_dir = any('Contacts/' in f for f in file_list)
                has_vcf_files = any(f.endswith('.vcf') for f in file_list)
                
                if not (has_contacts_dir or has_vcf_files):
                    return False, "No Contacts directory or VCard files found"
                
                # Count VCard files
                vcf_files = [f for f in file_list if f.endswith('.vcf')]
                
                # Count potential profile images
                image_files = [f for f in file_list 
                              if any(f.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])]
                
                contact_count = len(vcf_files)
                image_count = len(image_files)
                
                return True, f"Found {contact_count} contact files and {image_count} images"
                
        except zipfile.BadZipFile:
            return False, "Invalid zip file"
        except Exception as e:
            return False, f"Error reading zip file: {e}"
    
    def extract_contacts_and_images(self) -> Tuple[List[Dict[str, Any]], Dict[str, bytes]]:
        """Extract contacts and images from the Google Takeout zip file."""
        contacts = []
        images = {}
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Extract VCard files
                vcf_files = [f for f in file_list if f.endswith('.vcf')]
                
                for vcf_file in vcf_files:
                    try:
                        vcf_data = zip_ref.read(vcf_file).decode('utf-8')
                        contact_data = self._parse_vcard(vcf_data)
                        if contact_data:
                            contacts.append(contact_data)
                    except Exception as e:
                        print(f"Error parsing VCard {vcf_file}: {e}")
                        continue
                
                # Extract image files
                image_files = [f for f in file_list 
                              if any(f.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])]
                
                for image_file in image_files:
                    try:
                        image_data = zip_ref.read(image_file)
                        # Extract just the filename for mapping
                        filename = Path(image_file).name
                        images[filename] = image_data
                    except Exception as e:
                        print(f"Error extracting image {image_file}: {e}")
                        continue
                
                # Match images to contacts
                self._match_images_to_contacts(contacts, images)
                
        except Exception as e:
            print(f"Error processing zip file: {e}")
            
        return contacts, images
    
    def _parse_vcard(self, vcf_data: str) -> Optional[Dict[str, Any]]:
        """Parse a VCard string and extract contact information."""
        try:
            vcard = vobject.readOne(vcf_data)
            
            contact = {
                'first': '',
                'last': '',
                'emails': [],
                'phones': [],
                'profile_image': None,
                'profile_image_filename': None,
                'profile_image_mime_type': None
            }
            
            # Extract name
            if hasattr(vcard, 'fn'):
                full_name = vcard.fn.value.strip()
                # Try to split into first/last
                name_parts = full_name.split(' ', 1)
                contact['first'] = name_parts[0] if name_parts else ''
                contact['last'] = name_parts[1] if len(name_parts) > 1 else ''
            
            if hasattr(vcard, 'n'):
                # More structured name info
                name = vcard.n.value
                if hasattr(name, 'given'):
                    contact['first'] = name.given or contact['first']
                if hasattr(name, 'family'):
                    contact['last'] = name.family or contact['last']
            
            # Extract emails
            if hasattr(vcard, 'email_list'):
                for email in vcard.email_list:
                    email_value = email.value.strip()
                    if email_value:
                        contact['emails'].append(email_value)
            elif hasattr(vcard, 'email'):
                email_value = vcard.email.value.strip()
                if email_value:
                    contact['emails'].append(email_value)
            
            # Extract phone numbers
            if hasattr(vcard, 'tel_list'):
                for tel in vcard.tel_list:
                    phone_value = tel.value.strip()
                    if phone_value:
                        contact['phones'].append(phone_value)
            elif hasattr(vcard, 'tel'):
                phone_value = vcard.tel.value.strip()
                if phone_value:
                    contact['phones'].append(phone_value)
            
            # Extract photo if present
            if hasattr(vcard, 'photo'):
                # VCard photos can be embedded or referenced
                photo = vcard.photo
                if hasattr(photo, 'value'):
                    # This might be base64 encoded data
                    contact['embedded_photo'] = photo.value
            
            return contact
            
        except Exception as e:
            print(f"Error parsing VCard: {e}")
            return None
    
    def _match_images_to_contacts(self, contacts: List[Dict[str, Any]], images: Dict[str, bytes]):
        """Match profile images to contacts based on naming patterns."""
        # Google Takeout typically names profile images based on contact names
        # This is a heuristic approach since exact matching rules may vary
        
        for contact in contacts:
            # Create possible image filename patterns
            first = contact.get('first', '').strip()
            last = contact.get('last', '').strip()
            
            if not first and not last:
                continue
                
            # Common patterns for Google Takeout profile images
            possible_names = []
            
            if first and last:
                # "FirstName LastName.jpg"
                possible_names.append(f"{first} {last}.jpg")
                possible_names.append(f"{first} {last}.jpeg")
                possible_names.append(f"{first} {last}.png")
                # "FirstNameLastName.jpg" 
                possible_names.append(f"{first}{last}.jpg")
                possible_names.append(f"{first}{last}.jpeg")
                possible_names.append(f"{first}{last}.png")
                # "LastName, FirstName.jpg"
                possible_names.append(f"{last}, {first}.jpg")
                possible_names.append(f"{last}, {first}.jpeg")
                possible_names.append(f"{last}, {first}.png")
            elif first:
                possible_names.append(f"{first}.jpg")
                possible_names.append(f"{first}.jpeg")
                possible_names.append(f"{first}.png")
            elif last:
                possible_names.append(f"{last}.jpg")
                possible_names.append(f"{last}.jpeg")
                possible_names.append(f"{last}.png")
            
            # Look for matching image
            for name in possible_names:
                if name in images:
                    contact['profile_image'] = images[name]
                    contact['profile_image_filename'] = name
                    contact['profile_image_mime_type'] = mimetypes.guess_type(name)[0] or 'image/jpeg'
                    break
    
    def get_preview_info(self) -> Dict[str, Any]:
        """Get preview information about the takeout file."""
        is_valid, message = self.validate_takeout_file()
        
        if not is_valid:
            return {
                'valid': False,
                'error': message,
                'contact_count': 0,
                'image_count': 0,
                'sample_contacts': []
            }
        
        # Extract a preview
        contacts, images = self.extract_contacts_and_images()
        
        # Get first few contact names for preview
        sample_contacts = []
        for i, contact in enumerate(contacts[:5]):  # First 5 contacts
            first = contact.get('first', '')
            last = contact.get('last', '')
            name = f"{first} {last}".strip() or "(No name)"
            has_image = contact.get('profile_image') is not None
            sample_contacts.append({
                'name': name,
                'has_image': has_image
            })
        
        return {
            'valid': True,
            'contact_count': len(contacts),
            'image_count': len(images),
            'contacts_with_images': len([c for c in contacts if c.get('profile_image')]),
            'sample_contacts': sample_contacts,
            'message': message
        }


def find_takeout_files(data_dir: Path) -> List[Path]:
    """Find Google Takeout zip files in the data directory."""
    zip_files = list(data_dir.glob("*.zip"))
    
    # Filter to likely Google Takeout files
    takeout_files = []
    for zip_file in zip_files:
        # Google Takeout files often have "takeout" in the name
        if 'takeout' in zip_file.name.lower():
            takeout_files.append(zip_file)
        else:
            # Check if it's a valid takeout file by content
            parser = GoogleTakeoutParser(zip_file)
            is_valid, _ = parser.validate_takeout_file()
            if is_valid:
                takeout_files.append(zip_file)
    
    return takeout_files


def parse_takeout_contacts(zip_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Parse contacts from a Google Takeout zip file."""
    parser = GoogleTakeoutParser(zip_path)
    
    # Validate first
    is_valid, message = parser.validate_takeout_file()
    if not is_valid:
        return [], {'error': message}
    
    # Extract contacts and images
    contacts, images = parser.extract_contacts_and_images()
    
    # Get summary info
    info = {
        'contact_count': len(contacts),
        'image_count': len(images),
        'contacts_with_images': len([c for c in contacts if c.get('profile_image')]),
        'message': message
    }
    
    return contacts, info
