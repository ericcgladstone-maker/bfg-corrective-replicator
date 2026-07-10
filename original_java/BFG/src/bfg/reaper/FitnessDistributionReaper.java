package bfg.reaper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.MutationStep;
import bfg.RandomSelector;

public class FitnessDistributionReaper implements Reaper {
	private static final Logger log = LoggerFactory.getLogger(FitnessDistributionReaper.class);

	private int maxSize;

	public FitnessDistributionReaper(int maxSize) {
		this.maxSize = maxSize;
	}

	@Override
	public List<MutationStep> reap(List<MutationStep> generationList) {
		List<MutationStep> survivors;
		if (generationList.size() <= maxSize) {
			survivors = generationList;
		} else {
			survivors = getByFitnessDistribution(maxSize, generationList);
		}
		return survivors;
	}

	private List<MutationStep> getByFitnessDistribution(int max, List<MutationStep> source) {
		Map<Double, List<MutationStep>> buckets = createBuckets(source);
		log.debug("Created {} buckets", buckets.size());
		Map<Double, Double> percentages = analyzeBuckets(buckets);
		ArrayList<MutationStep> workspace = new ArrayList<>();
		RandomSelector<MutationStep> selector = new RandomSelector<MutationStep>();
		for (Double fitnessScore : percentages.keySet()) {
			List<MutationStep> childrenWithFitness = buckets.get(fitnessScore);
			Double fractionDesired = percentages.get(fitnessScore);
			int childrenKept = (int) Math.floor(max * fractionDesired);
			log.trace("Keeping {} / {} ({}%) with fitness {}", childrenKept, childrenWithFitness.size(),
					fractionDesired * 100.0, fitnessScore);
			workspace.addAll(selector.select(childrenKept, childrenWithFitness));
		}
		return workspace;
	}

	private Map<Double, Double> analyzeBuckets(Map<Double, List<MutationStep>> buckets) {
		int totalElements = 0;
		Map<Double, Double> results = new HashMap<>();
		for (Double fitnessScore : buckets.keySet()) {
			int childrenWithFitness = buckets.get(fitnessScore).size();
			totalElements += childrenWithFitness;
			results.put(fitnessScore, 1.0 * childrenWithFitness);
		}
		for (Double fitnessScore : results.keySet()) {
			results.put(fitnessScore, results.get(fitnessScore) / totalElements);
		}
		return results;
	}

	private Map<Double, List<MutationStep>> createBuckets(List<MutationStep> source) {
		Map<Double, List<MutationStep>> buckets = new HashMap<>();
		for (MutationStep step : source) {
			Double fitnessScore = step.getConvergingToFitness();
			List<MutationStep> bucketList = buckets.get(fitnessScore);
			if (bucketList == null) {
				bucketList = new ArrayList<>();
				buckets.put(fitnessScore, bucketList);
			}
			bucketList.add(step);
		}
		return buckets;
	}

	@Override
	public String description() {
		return "Distribution reaper keeping " + maxSize + " elements";
	}

}
