//
//  Views.swift
//  Trailmark — eval fixture: the screens the App Store asset set may show.
//

import SwiftUI

struct Hike: Identifiable, Hashable {
    let id = UUID()
    let name: String
    let distanceKm: Double
    let minutes: Int
    let elevationM: Int
    var isFavorite: Bool
}

extension Hike {
    static let samples: [Hike] = [
        Hike(name: "Ridge Loop", distanceKm: 6.2, minutes: 130, elevationM: 410, isFavorite: true),
        Hike(name: "Lakeside Path", distanceKm: 4.8, minutes: 85, elevationM: 60, isFavorite: false),
        Hike(name: "Pine Forest Trail", distanceKm: 9.1, minutes: 185, elevationM: 520, isFavorite: true),
        Hike(name: "Coastal Cliffs", distanceKm: 7.4, minutes: 150, elevationM: 230, isFavorite: false),
    ]
}

// MARK: - Root

struct RootView: View {
    @Environment(\.horizontalSizeClass) private var sizeClass

    var body: some View {
        if sizeClass == .regular {
            // iPad: sidebar + detail
            NavigationSplitView {
                TrailListView()
            } detail: {
                TrailDetailView(hike: Hike.samples[0])
            }
        } else {
            TabView {
                TrailListView().tabItem { Label("Trails", systemImage: "list.bullet") }
                StatsView().tabItem { Label("Stats", systemImage: "chart.bar.fill") }
                SettingsView().tabItem { Label("Settings", systemImage: "gearshape") }
            }
            .tint(Color("AccentColor"))
        }
    }
}

// MARK: - Trail log

struct TrailListView: View {
    @State private var query = ""

    var body: some View {
        NavigationStack {
            List(Hike.samples) { hike in
                NavigationLink(value: hike) {
                    HStack(spacing: 12) {
                        Image(systemName: "mappin.circle.fill")
                            .font(.title2)
                            .foregroundStyle(Color("AccentColor"))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(hike.name).font(.body)
                            Text("\(hike.distanceKm, specifier: "%.1f") km · \(hike.minutes / 60) h \(hike.minutes % 60) min")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        if hike.isFavorite {
                            Image(systemName: "star.fill").foregroundStyle(.yellow)
                        }
                    }
                }
            }
            .navigationTitle("Trails")
            .searchable(text: $query, prompt: "Search trails")
            .navigationDestination(for: Hike.self) { TrailDetailView(hike: $0) }
            .toolbar { Button("New Hike", systemImage: "plus") {} }
        }
    }
}

// MARK: - Trail detail + live hike

struct TrailDetailView: View {
    let hike: Hike
    @State private var isRecording = false

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Grid(horizontalSpacing: 12, verticalSpacing: 12) {
                    GridRow {
                        StatTile(label: "Distance", value: "\(hike.distanceKm) km")
                        StatTile(label: "Time", value: "\(hike.minutes / 60) h \(hike.minutes % 60)")
                    }
                    GridRow {
                        StatTile(label: "Elevation", value: "\(hike.elevationM) m")
                        StatTile(label: "Pace", value: "21 min/km")
                    }
                }
                Button(isRecording ? "Stop Hike" : "Start Hike") { isRecording.toggle() }
                    .buttonStyle(.borderedProminent)
                    .tint(isRecording ? .red : Color("AccentColor"))
                    .controlSize(.large)
                if isRecording {
                    Text("Recording · 00:42:17")
                        .font(.title3.monospacedDigit())
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
        }
        .navigationTitle(hike.name)
        .toolbar { Button("Favorite", systemImage: hike.isFavorite ? "star.fill" : "star") {} }
    }
}

struct StatTile: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label.uppercased()).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
            Text(value).font(.title2.bold().monospacedDigit())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }
}

// MARK: - Stats

struct StatsView: View {
    private let week: [(day: String, km: Double)] = [
        ("Mon", 0), ("Tue", 4.8), ("Wed", 0), ("Thu", 6.2), ("Fri", 0), ("Sat", 9.1), ("Sun", 7.4),
    ]

    var body: some View {
        NavigationStack {
            List {
                Section("This week") {
                    HStack(alignment: .bottom, spacing: 10) {
                        ForEach(week, id: \.day) { entry in
                            VStack {
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(Color("AccentColor"))
                                    .frame(width: 22, height: max(4, entry.km * 12))
                                Text(entry.day).font(.caption2).foregroundStyle(.secondary)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                    Text("27.5 km walked this week").font(.headline)
                }
                Section("All time") {
                    LabeledContent("Hikes", value: "48")
                    LabeledContent("Distance", value: "312 km")
                    LabeledContent("Elevation gain", value: "14,200 m")
                }
            }
            .navigationTitle("Stats")
        }
    }
}

// MARK: - Settings

struct SettingsView: View {
    @AppStorage("useMetric") private var useMetric = true

    var body: some View {
        NavigationStack {
            Form {
                Section("Units") {
                    Toggle("Metric units", isOn: $useMetric)
                }
                Section {
                    LabeledContent("Apple Health sync", value: "Coming soon")
                        .foregroundStyle(.secondary)
                } footer: {
                    Text("Hikes are stored on this device only.")
                }
            }
            .navigationTitle("Settings")
        }
    }
}
