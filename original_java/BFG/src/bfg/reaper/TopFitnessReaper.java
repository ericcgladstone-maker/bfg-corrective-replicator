package bfg.reaper;

import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

import bfg.MutationStep;

public class TopFitnessReaper implements Reaper {
	private final int maxSize;

	public TopFitnessReaper(int maxSize) {
		this.maxSize = maxSize;
	}

	@Override
	public List<MutationStep> reap(List<MutationStep> steps) {
		return reapAsStream(steps);
	}

	private List<MutationStep> reapAsStream(List<MutationStep> steps) {
		List<MutationStep> survivors = steps.parallelStream()
				.sorted(Comparator.comparing(MutationStep::getConvergingToFitness).reversed()).limit(maxSize)
				.collect(Collectors.toList());
		survivors.parallelStream().forEach(survivor -> survivor.setSurvivalTarget(survivor.getConvergingToString()));
		return survivors;
	}

	@Override
	public String description() {
		return "Top scores reaper keeping " + maxSize + " elements";
	}

}
