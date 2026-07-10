package bfg;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.RecursiveTask;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.replicator.Replicator;

public class EvolutionProcessor extends RecursiveTask<List<MutationStep>> {
	private static final Logger log = LoggerFactory.getLogger(EvolutionProcessor.class);
	private static final long serialVersionUID = -3752199085527678513L;

	private MutationStep[] mutationSteps;
	private Replicator replicator;

	public EvolutionProcessor(Replicator replicator, List<MutationStep> mutationList) {
		this.replicator = replicator;
		mutationSteps = mutationList.toArray(new MutationStep[0]);
	}

	public EvolutionProcessor(Replicator replicator, MutationStep[] mutations) {
		this.replicator = replicator;
		mutationSteps = mutations;
	}

	@Override
	protected List<MutationStep> compute() {
		if (mutationSteps.length == 0) {
			return Collections.emptyList();
		} else if (mutationSteps.length == 1) {
			return new ArrayList<MutationStep>(replicator.replicate(mutationSteps[0]));
		} else {
			log.trace("Computing size: {}", mutationSteps.length);
			int midpoint = mutationSteps.length / 2;
			MutationStep[] leftSteps = Arrays.copyOfRange(mutationSteps, 0, midpoint);
			MutationStep[] rightSteps = Arrays.copyOfRange(mutationSteps, midpoint, mutationSteps.length);
			EvolutionProcessor left = new EvolutionProcessor(replicator, leftSteps);
			left.fork();
			EvolutionProcessor right = new EvolutionProcessor(replicator, rightSteps);
			ArrayList<MutationStep> computedMutationList = new ArrayList<MutationStep>(right.compute());
			computedMutationList.addAll(left.join());
			log.trace("Computed mutations: {}", computedMutationList.size());
			return computedMutationList;
		}
	}

}
