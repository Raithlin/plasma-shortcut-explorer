# Distro PySide6 supplies the import but does not always use PyPI's split name.
%global __requires_exclude ^.*pyside6-essentials.*$
Name:           plasma-shortcut-explorer
Version:        0.1.0
Release:        1%{?dist}
Summary:        Search the global shortcuts configured in KDE Plasma 6
License:        MIT
URL:            https://github.com/Raithlin/plasma-shortcut-explorer
Source0:        plasma_shortcut_explorer-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel >= 3.11
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  python3-pytest
BuildRequires:  python3-coverage
BuildRequires:  python3-pyside6 >= 6.6
BuildRequires:  python3-dbus-next
BuildRequires:  dbus-daemon
Requires:       python3 >= 3.11
Requires:       python3-pyside6 >= 6.6
Requires:       python3-dbus-next >= 0.2.3
Requires:       qt6-qtwayland
Requires:       kglobalacceld >= 6.0
Recommends:     systemsettings

%description
A lightweight overlay showing current KGlobalAccel bindings grouped by category,
with fuzzy search and keyboard navigation. Requires a KDE Plasma 6 session.

%prep
%autosetup -n plasma_shortcut_explorer-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files kde_shortcuts

%check
KDE_SHORTCUTS_PYTHON=%{__python3} scripts/test.sh -q

%files -f %{pyproject_files}
%license LICENSE
%doc README.md DESIGN.md
%{_bindir}/plasma-shortcut-explorer
%{_bindir}/kde-shortcuts
%{_datadir}/applications/org.kde.shortcutexplorer.desktop
%{_datadir}/icons/hicolor/scalable/apps/org.kde.shortcutexplorer.svg
%{_datadir}/metainfo/org.kde.shortcutexplorer.metainfo.xml

%changelog
* Sun Oct 18 2026 Stephen Metcalfe <raithlin@outlook.com> - 0.1.0-1
- Initial packaging
