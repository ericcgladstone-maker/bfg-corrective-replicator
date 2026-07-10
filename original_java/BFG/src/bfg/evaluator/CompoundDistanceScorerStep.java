package bfg.evaluator;

public class CompoundDistanceScorerStep {
	private final StringSimilarityScorer scorer;
	private final double weight;

	public CompoundDistanceScorerStep(StringSimilarityScorer scorer, double weight) {
		this.scorer = scorer;
		this.weight = weight;
	}

	public StringSimilarityScorer getScorer() {
		return scorer;
	}

	public double getWeight() {
		return weight;
	}
}
