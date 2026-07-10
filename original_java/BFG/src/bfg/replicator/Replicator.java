package bfg.replicator;

import java.util.Arrays;
import java.util.List;
import java.util.function.IntFunction;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.MutationStep;
import bfg.mutator.Mutator;

public class Replicator {
	private static final Logger log = LoggerFactory.getLogger(Replicator.class);
	private final int childrenCount;
	private final Mutator mutator;

	public Replicator(int childrenCount, Mutator mutator) {
		this.childrenCount = childrenCount;
		this.mutator = mutator;
	}

	public List<MutationStep> replicate(final MutationStep step) {
		MutationStep[] children = new MutationStep[childrenCount];
		Arrays.parallelSetAll(children, new IntFunction<MutationStep>() {
			@Override
			public MutationStep apply(int value) {
				MutationStep child = new MutationStep(step);
				mutator.mutate(child);
				log.debug("Mutated");
				return child;
			}
		});
		log.debug("Replicated {}", children.length);
		return Arrays.asList(children);
	}
}
