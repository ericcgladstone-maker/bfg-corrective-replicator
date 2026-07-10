package bfg.reaper;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.PriorityBlockingQueue;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.MutationStep;
import bfg.misc.StringSanitizer;

public class BucketReaper implements Reaper {
	private static final Logger log = LoggerFactory.getLogger(BucketReaper.class);

	private Map<String, Integer> bucketCapacities = new HashMap<>();
	private Map<String, Double> minDiversionFitness = new HashMap<>();
	private int survivorMax;

	public BucketReaper(List<String> targets, List<Integer> capacities, List<Double> diversionFitness,
			int maxTotalInGeneration) {
		StringSanitizer sanitizer = StringSanitizer.getInstance();
		Iterator<String> targetsIterator = targets.iterator();
		Iterator<Integer> capacitiesIterator = capacities.iterator();
		Iterator<Double> diversionIterator = diversionFitness.iterator();
		while (targetsIterator.hasNext() && capacitiesIterator.hasNext()) {
			String sanitizedTarget = sanitizer.sanitize(targetsIterator.next());
			bucketCapacities.put(sanitizedTarget, capacitiesIterator.next());
			minDiversionFitness.put(sanitizedTarget, diversionIterator.next());
		}
		survivorMax = maxTotalInGeneration;
	}

	@Override
	public String description() {
		return "Bucket reaper with " + bucketCapacities.size() + " targets";
	}

	@Override
	public List<MutationStep> reap(List<MutationStep> generationList) {
		// Create queues for each target. Each queue is priority by fitness score to
		// that target.
		class MutationStepTargetScoreComparator implements Comparator<MutationStep> {
			private final String target;

			public MutationStepTargetScoreComparator(String target) {
				super();
				this.target = target;
			}

			@Override
			public int compare(MutationStep o1, MutationStep o2) {
				return -Double.compare(o1.getFitnessScore(target), o2.getFitnessScore(target));
			}
		}
		Map<String, Queue<MutationStep>> scoreQueues = new ConcurrentHashMap<>();
		bucketCapacities.keySet().stream().forEach(targetSentence -> {
			scoreQueues.put(targetSentence,
					new PriorityBlockingQueue<>(10, new MutationStepTargetScoreComparator(targetSentence)));
		});
		// Push each MutationStep into all the queues
		generationList.parallelStream().forEach(mutationStep -> {
			bucketCapacities.keySet().stream().forEach(targetSentence -> {
				scoreQueues.get(targetSentence).add(mutationStep);
			});
		});
		// Create survivor set
		// Survivor selection will take the highest relative fitness MutationStep as
		// long as there are slots to be taken for that target.
		// Relative fitness is fitness of a MutationStep against the target of the
		// queue.
		// Survivor selection needs to look at all queues so it must be single threaded.
		Set<MutationStep> survivors = new HashSet<>();
		Map<String, Integer> runningCapacity = new HashMap<>(bucketCapacities);
		boolean survivorSpaceFilled = false;
		while (!survivorSpaceFilled) {
			String targetString = findHighestRelativeFitnessTarget(scoreQueues, runningCapacity.keySet());
			MutationStep survivorCandidate = takeSurvivorCandidate(scoreQueues, targetString);
			if (survivorCandidate != null) {
				// survivor candidate found
				if (survivorCandidate.getConvergingToString().equals(targetString) //
						|| //
						survivorCandidate.getFitnessScore(targetString) > minDiversionFitness.get(targetString) //
						|| //
						true //
				) {
					// survivor is converging to target string
					// or survivor candidate has minimum fitness for diversion to target
					if (survivors.add(survivorCandidate)) {
						// successfully added because it was not already a survivor
						reduceCapacity(runningCapacity, targetString);
						survivorCandidate.setSurvivalTarget(targetString);
					}
				}
			}
			boolean scoreQueuesEmpty = scoreQueues.isEmpty();
			boolean runningCapacityEmpty = runningCapacity.isEmpty();
			boolean allGenerationSurvives = survivors.size() >= generationList.size();
			boolean generationSpaceExceeded = survivors.size() >= survivorMax;
			log.debug(
					"Survivor for {} : scoreQueuesEmpty={}, runningCapacityEmpty={}, allGenerationSurvives={}, generationSpaceExceeded={}",
					targetString, scoreQueuesEmpty, runningCapacityEmpty, allGenerationSurvives,
					generationSpaceExceeded);
			survivorSpaceFilled = scoreQueuesEmpty || runningCapacityEmpty || allGenerationSurvives
					|| generationSpaceExceeded;
		}
		return new ArrayList<>(survivors);
	}

	private MutationStep takeSurvivorCandidate(Map<String, Queue<MutationStep>> scoreQueues, String targetString) {
		MutationStep retVal = null;
		Queue<MutationStep> survivorCandidateQueue = scoreQueues.get(targetString);
		if (survivorCandidateQueue != null) {
			retVal = survivorCandidateQueue.remove();
			if (survivorCandidateQueue.isEmpty()) {
				scoreQueues.remove(targetString);
			}
		}
		return retVal;
	}

	private void reduceCapacity(Map<String, Integer> runningCapacity, String targetString) {
		Integer currentCapacity = runningCapacity.get(targetString);
		if (currentCapacity != null) {
			if (currentCapacity > 1) {
				runningCapacity.put(targetString, currentCapacity - 1);
			} else {
				runningCapacity.remove(targetString);
			}
		}
	}

	private String findHighestRelativeFitnessTarget(Map<String, Queue<MutationStep>> scoreQueues,
			Set<String> targetsWithCapacity) {
		double highFitnessValue = 0.0d;
		String highFitnessTarget = "";
		Iterator<String> targetIterator = targetsWithCapacity.iterator();
		while (targetIterator.hasNext()) {
			String target = targetIterator.next();
			MutationStep thisStep;
			try {
				thisStep = scoreQueues.get(target).peek();
			} catch (NullPointerException ex) {
				String message = "No capacity for target ::" + target + "::";
				log.debug(message, ex);
				thisStep = null;
			}
			if (thisStep != null) {
				double thisFitness = thisStep.getFitnessScore(target);
				if (thisFitness > highFitnessValue) {
					highFitnessTarget = target;
					highFitnessValue = thisFitness;
				}
			}
		}
		assert !highFitnessTarget.equals("");
		return highFitnessTarget;
	}
}
