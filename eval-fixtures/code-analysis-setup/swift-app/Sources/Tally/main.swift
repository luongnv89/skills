struct Counter {
    private(set) var value = 0

    mutating func increment(by step: Int = 1) {
        value += step
    }
}

var counter = Counter()
for _ in 0..<3 {
    counter.increment()
}
print("Tally: \(counter.value)")
