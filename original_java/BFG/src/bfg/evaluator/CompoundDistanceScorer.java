package bfg.evaluator;

import java.util.Arrays;
import java.util.List;

import com.google.common.base.Joiner;
import com.google.common.collect.ImmutableList;

public class CompoundDistanceScorer implements StringSimilarityScorer {
	private final List<CompoundDistanceScorerStep> steps;

	public CompoundDistanceScorer(CompoundDistanceScorerStep step, CompoundDistanceScorerStep... steps) {
		this.steps = ImmutableList.<CompoundDistanceScorerStep>builder().add(step).addAll(Arrays.asList(steps)).build();
	}

	@Override
	public double similarity(String str1, String str2) {
		double totalWeight = 0.0;
		double runningScore = 0.0;
		for (CompoundDistanceScorerStep step : this.steps) {
			double stepWeight = step.getWeight();
			StringSimilarityScorer stepScorer = step.getScorer();
			totalWeight += stepWeight;
			runningScore += stepWeight * stepScorer.similarity(str1, str2);
		}
		return runningScore / totalWeight;
	}

	@Override
	public String description() {
		return "Compound scorer: " + Joiner.on(", ").join(steps.stream()
				.map(s -> "[" + s.getScorer().description() + " weight " + s.getWeight() + "]").iterator());
	}

}
