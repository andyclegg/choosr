"""Tests for profile caching functionality."""

import os
import tempfile
import time


from browser import ProfileCache, Profile, ProfileIcon


class TestProfileCache:
    """Tests for ProfileCache class."""

    def test_init_creates_cache_file_path(self):
        """Test cache initialization with default file path."""
        cache = ProfileCache()
        expected_path = os.path.expanduser("~/.choosr-cache.json")
        assert cache.cache_file == expected_path

    def test_init_custom_cache_file(self):
        """Test cache initialization with custom file path."""
        custom_path = "/tmp/test-cache.json"
        cache = ProfileCache(custom_path)
        assert cache.cache_file == custom_path

    def test_load_cache_nonexistent_file(self):
        """Test loading cache when file doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_path = temp_file.name

        # File is now deleted
        cache = ProfileCache(temp_path)
        assert cache._cache_data == {}

    def test_load_cache_invalid_json(self):
        """Test loading cache with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("invalid json content")
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)
            assert cache._cache_data == {}
        finally:
            os.unlink(temp_path)

    def test_cache_and_retrieve_profiles(self):
        """Test caching and retrieving profiles."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)

            # Create test profiles
            icon = ProfileIcon(background_color="#FF0000", text_color="#FFFFFF")
            profiles = [
                Profile("profile1", "Profile 1", "chrome", is_private=False, icon=icon),
                Profile("profile2", "Profile 2", "chrome", is_private=True),
            ]

            # Cache profiles
            source_files = ["/fake/source.json"]
            cache.cache_profiles("chrome", profiles, source_files)

            # Retrieve cached profiles
            cached = cache.get_cached_profiles("chrome", source_files)

            assert cached is not None
            assert len(cached) == 2
            assert cached[0].id == "profile1"
            assert cached[0].name == "Profile 1"
            assert cached[0].browser == "chrome"
            assert cached[0].is_private is False
            assert cached[0].icon.background_color == "#FF0000"
            assert cached[1].id == "profile2"
            assert cached[1].is_private is True

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_cache_invalidation_newer_source_file(self):
        """Test cache invalidation when source file is newer."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        with tempfile.NamedTemporaryFile(delete=False) as source_file:
            source_path = source_file.name

        try:
            cache = ProfileCache(temp_path)

            profiles = [Profile("profile1", "Profile 1", "chrome")]
            source_files = [source_path]

            # Cache profiles
            cache.cache_profiles("chrome", profiles, source_files)

            # Verify cache works
            cached = cache.get_cached_profiles("chrome", source_files)
            assert cached is not None

            # Wait a moment and update source file
            time.sleep(0.1)
            with open(source_path, "w") as f:
                f.write("updated content")

            # Cache should now be invalid
            cached = cache.get_cached_profiles("chrome", source_files)
            assert cached is None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(source_path):
                os.unlink(source_path)

    def test_cache_invalidation_missing_source_file(self):
        """Test cache behavior when source file doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)

            profiles = [Profile("profile1", "Profile 1", "chrome")]
            source_files = ["/nonexistent/file.json"]

            # Cache profiles with nonexistent source file
            cache.cache_profiles("chrome", profiles, source_files)

            # Should still return cached data since source file doesn't exist
            cached = cache.get_cached_profiles("chrome", source_files)
            assert cached is not None
            assert len(cached) == 1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_invalidate_browser(self):
        """Test invalidating cache for specific browser."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)

            # Cache profiles for two browsers
            chrome_profiles = [Profile("profile1", "Profile 1", "chrome")]
            firefox_profiles = [Profile("profile2", "Profile 2", "firefox")]

            cache.cache_profiles("chrome", chrome_profiles, ["/fake/chrome.json"])
            cache.cache_profiles("firefox", firefox_profiles, ["/fake/firefox.ini"])

            # Verify both are cached
            assert (
                cache.get_cached_profiles("chrome", ["/fake/chrome.json"]) is not None
            )
            assert (
                cache.get_cached_profiles("firefox", ["/fake/firefox.ini"]) is not None
            )

            # Invalidate Chrome cache
            cache.invalidate_browser("chrome")

            # Chrome should be invalidated, Firefox should remain
            assert cache.get_cached_profiles("chrome", ["/fake/chrome.json"]) is None
            assert (
                cache.get_cached_profiles("firefox", ["/fake/firefox.ini"]) is not None
            )

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_clear_all(self):
        """Test clearing all cached data."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)

            # Cache profiles for multiple browsers
            cache.cache_profiles(
                "chrome", [Profile("p1", "P1", "chrome")], ["/fake/chrome.json"]
            )
            cache.cache_profiles(
                "firefox", [Profile("p2", "P2", "firefox")], ["/fake/firefox.ini"]
            )

            # Verify data is cached
            assert len(cache._cache_data) == 2

            # Clear all
            cache.clear_all()

            # All data should be gone
            assert cache._cache_data == {}
            assert cache.get_cached_profiles("chrome", ["/fake/chrome.json"]) is None
            assert cache.get_cached_profiles("firefox", ["/fake/firefox.ini"]) is None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            cache = ProfileCache(temp_path)

            # Cache profiles for multiple browsers
            chrome_profiles = [
                Profile("p1", "P1", "chrome"),
                Profile("p2", "P2", "chrome"),
            ]
            firefox_profiles = [Profile("p3", "P3", "firefox")]

            cache.cache_profiles("chrome", chrome_profiles, ["/fake/chrome.json"])
            cache.cache_profiles("firefox", firefox_profiles, ["/fake/firefox.ini"])

            # Get stats
            stats = cache.get_cache_stats()

            assert "chrome" in stats
            assert "firefox" in stats
            assert stats["chrome"]["profile_count"] == 2
            assert stats["firefox"]["profile_count"] == 1
            assert stats["chrome"]["source_files"] == ["/fake/chrome.json"]
            assert stats["firefox"]["source_files"] == ["/fake/firefox.ini"]
            assert "timestamp" in stats["chrome"]
            assert "timestamp" in stats["firefox"]

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_cache_creates_directory(self):
        """Test that saving cache creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "subdir", "cache.json")
            cache = ProfileCache(cache_path)

            # Cache some data to trigger save
            profiles = [Profile("p1", "P1", "chrome")]
            cache.cache_profiles("chrome", profiles, ["/fake/source.json"])

            # Directory and file should be created
            assert os.path.exists(cache_path)
            assert os.path.isdir(os.path.dirname(cache_path))


class TestProfileIconSerialization:
    """Tests for ProfileIcon serialization."""

    def test_to_dict(self):
        """Test ProfileIcon to_dict method."""
        icon = ProfileIcon(
            avatar_icon="test-icon",
            background_color="#FF0000",
            text_color="#FFFFFF",
            icon_data=b"test data",
            icon_file_path="/path/to/icon.png",
        )

        result = icon.to_dict()
        expected = {
            "avatar_icon": "test-icon",
            "background_color": "#FF0000",
            "text_color": "#FFFFFF",
            "icon_data": b"test data",
            "icon_file_path": "/path/to/icon.png",
        }
        assert result == expected

    def test_from_dict(self):
        """Test ProfileIcon from_dict method."""
        data = {
            "avatar_icon": "test-icon",
            "background_color": "#FF0000",
            "text_color": "#FFFFFF",
            "icon_data": b"test data",
            "icon_file_path": "/path/to/icon.png",
        }

        icon = ProfileIcon.from_dict(data)
        assert icon.avatar_icon == "test-icon"
        assert icon.background_color == "#FF0000"
        assert icon.text_color == "#FFFFFF"
        assert icon.icon_data == b"test data"
        assert icon.icon_file_path == "/path/to/icon.png"


class TestProfileSerialization:
    """Tests for Profile serialization."""

    def test_to_dict_with_icon(self):
        """Test Profile to_dict method with icon."""
        icon = ProfileIcon(background_color="#FF0000")
        profile = Profile(
            id="test-id",
            name="Test Profile",
            browser="chrome",
            is_private=True,
            icon=icon,
        )

        result = profile.to_dict()
        assert result["id"] == "test-id"
        assert result["name"] == "Test Profile"
        assert result["browser"] == "chrome"
        assert result["is_private"] is True
        assert "icon" in result
        assert result["icon"]["background_color"] == "#FF0000"

    def test_to_dict_without_icon(self):
        """Test Profile to_dict method without icon."""
        profile = Profile(
            id="test-id", name="Test Profile", browser="chrome", is_private=False
        )

        result = profile.to_dict()
        assert result["id"] == "test-id"
        assert result["name"] == "Test Profile"
        assert result["browser"] == "chrome"
        assert result["is_private"] is False
        assert result["icon"] is None

    def test_from_dict_with_icon(self):
        """Test Profile from_dict method with icon."""
        data = {
            "id": "test-id",
            "name": "Test Profile",
            "browser": "chrome",
            "is_private": True,
            "icon": {"background_color": "#FF0000", "text_color": "#FFFFFF"},
        }

        profile = Profile.from_dict(data)
        assert profile.id == "test-id"
        assert profile.name == "Test Profile"
        assert profile.browser == "chrome"
        assert profile.is_private is True
        assert profile.icon is not None
        assert profile.icon.background_color == "#FF0000"
        assert profile.icon.text_color == "#FFFFFF"

    def test_from_dict_without_icon(self):
        """Test Profile from_dict method without icon."""
        data = {
            "id": "test-id",
            "name": "Test Profile",
            "browser": "chrome",
            "is_private": False,
        }

        profile = Profile.from_dict(data)
        assert profile.id == "test-id"
        assert profile.name == "Test Profile"
        assert profile.browser == "chrome"
        assert profile.is_private is False
        assert profile.icon is None
