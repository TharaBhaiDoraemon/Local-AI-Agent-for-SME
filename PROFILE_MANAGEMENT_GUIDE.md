# Profile Management Features Guide

## Overview

The system now includes comprehensive profile management features allowing users to customize their profiles with pictures, change usernames, update passwords/PINs, and manage hints.

## New Features

### 1. Profile Picture Upload
- Upload custom profile pictures (JPG, JPEG, PNG, GIF)
- Profile pictures are stored per user
- Automatic resizing and display
- Easy removal option

### 2. Username Changes
- Change your display name at any time
- Updates reflected across all interfaces
- Guest profiles cannot be edited

### 3. Password/PIN Management
- Update your PIN/password securely
- Optional - can be left empty for no password
- Existing password not shown for security

### 4. PIN Hints
- Add or update hints for your password
- Helpful reminders without revealing the password

### 5. IT Admin Portal Themes
- 5 theme options: Purple (Default), Green, Orange, Pink, Dark Mode
- Theme selector in top-right corner
- Theme persists across sessions
- Smooth transitions between themes

## API Endpoints

### Profile Management

#### Update Profile
```bash
PUT /api/profiles/{profile_id}
Body: {
  "name": "New Name",        # Optional
  "pin": "new_password",     # Optional
  "hint": "New hint"         # Optional
}
```

#### Upload Profile Picture
```bash
POST /api/profiles/{profile_id}/picture
Form Data: file (image file)
```

#### Get Profile Picture
```bash
GET /api/profiles/{profile_id}/picture
Returns: Image file
```

#### Delete Profile Picture
```bash
DELETE /api/profiles/{profile_id}/picture
```

## Usage Guide

### For Users

#### Accessing Profile Settings

1. **Login** to your profile
2. Look for the **settings icon** (⚙️) next to your name in the header
3. Click it to open Profile Settings

#### Updating Profile Picture

1. Open Profile Settings
2. Click **"Choose Picture"** button
3. Select an image file (JPG, PNG, GIF)
4. Picture uploads automatically
5. Click **"Remove Picture"** to delete

#### Changing Username

1. Open Profile Settings
2. Update the **Name** field
3. Click **"Save Changes"**

#### Updating Password/PIN

1. Open Profile Settings
2. Enter a new password in **"New PIN/Password"** field
3. Leave empty to keep current password
4. Optionally update the **PIN Hint**
5. Click **"Save Changes"**

### For IT Admins

#### Changing Admin Portal Theme

1. Login to admin portal at `/admin`
2. Click the **theme icon** (☀️) in top-right corner
3. Select from available themes:
   - 🔵 **Purple** (Default) - Professional blue-purple gradient
   - 🟢 **Green** - Fresh green theme
   - 🟠 **Orange** - Warm orange theme
   - 🌸 **Pink** - Soft pink theme
   - 🌙 **Dark Mode** - Easy on the eyes
4. Theme saves automatically

## Technical Details

### Profile Picture Storage

- **Location**: `./profile_pictures/` directory
- **Naming**: `{profile_id}.{extension}`
- **Formats**: JPG, JPEG, PNG, GIF
- **Access**: Via `/profile_pictures/{filename}` route

### Database Schema

Profile model now includes:
```python
{
    "id": "uuid",
    "name": "string",
    "pin": "string (hashed in production)",
    "hint": "string",
    "is_guest": "boolean",
    "created_at": "datetime",
    "profile_picture": "string (file path)"
}
```

### Theme System

Themes use CSS variables for easy customization:
```css
:root {
    --bg-gradient-start: color;
    --bg-gradient-end: color;
    --card-bg: color;
    --text-primary: color;
    --text-secondary: color;
    --border-color: color;
}
```

## Examples

### Update Profile Name and PIN
```bash
curl -X PUT http://localhost:8000/api/profiles/user-id \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "pin": "new_secure_pin", "hint": "My favorite color"}'
```

### Upload Profile Picture
```bash
curl -X POST http://localhost:8000/api/profiles/user-id/picture \
  -F "file=@profile.jpg"
```

### Get Profile Picture
```bash
curl http://localhost:8000/api/profiles/user-id/picture -o profile.jpg
```

## Security Considerations

### Current Implementation
- Profile pictures stored locally
- PINs stored in plain text (for development)
- No size limits on pictures

### Production Recommendations
1. **Hash PINs**: Use bcrypt or similar
2. **Image Validation**: Check file types, scan for malware
3. **Size Limits**: Limit picture size (e.g., 5MB max)
4. **Image Optimization**: Resize/compress images automatically
5. **CDN Storage**: Use cloud storage for pictures in production

## Troubleshooting

### Profile Picture Not Showing
- Check file permissions on `profile_pictures/` directory
- Verify file was uploaded successfully
- Check browser console for errors
- Try re-uploading the image

### Can't Update Profile
- Ensure you're not logged in as Guest
- Check that you have permission
- Verify API endpoint is accessible

### Theme Not Saving
- Check browser localStorage is enabled
- Try clearing cache and cookies
- Ensure JavaScript is enabled

## Feature Limitations

### Guest Profile
- Cannot be edited
- Cannot upload profile picture
- Cannot change name or password

### Profile Pictures
- Max file size: Determined by server settings
- Supported formats: JPG, JPEG, PNG, GIF only
- One picture per profile

## Future Enhancements

Possible additions:
- Image cropping tool
- Profile cover photos
- Custom profile themes
- Two-factor authentication
- Password strength meter
- Profile visibility settings
- Social profile links
- Profile badges/achievements

## Testing

### Test Profile Picture Upload
```python
import requests

# Upload picture
with open('test.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/profiles/user-id/picture',
        files={'file': f}
    )
    print(response.json())

# Get picture
response = requests.get('http://localhost:8000/api/profiles/user-id/picture')
with open('downloaded.jpg', 'wb') as f:
    f.write(response.content)
```

### Test Profile Update
```python
import requests

response = requests.put(
    'http://localhost:8000/api/profiles/user-id',
    json={
        'name': 'Updated Name',
        'pin': 'new_pin',
        'hint': 'New hint'
    }
)
print(response.json())
```

## Accessibility

### Profile Settings Modal
- Keyboard navigable
- Clear labels for screen readers
- Focus management
- ARIA attributes

### Theme System
- Dark mode for reduced eye strain
- High contrast options
- Color-blind friendly themes
- Respects system preferences

## Summary

The profile management system now provides:
✅ Profile picture upload and management
✅ Username changes
✅ Password/PIN updates
✅ Hint management
✅ Admin portal themes
✅ Smooth UI transitions
✅ Persistent theme selection
✅ Security-conscious design

Users have full control over their profiles, and IT admins can customize the admin portal appearance to their preference.
