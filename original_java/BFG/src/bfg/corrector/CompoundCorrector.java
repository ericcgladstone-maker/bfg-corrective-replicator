package bfg.corrector;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.stream.Collectors;

import org.apache.commons.rng.sampling.DiscreteProbabilityCollectionSampler;
import org.apache.commons.rng.simple.JDKRandomWrapper;

import com.google.common.base.Joiner;
import com.google.common.collect.ImmutableList;

import bfg.MutationStep;

public class CompoundCorrector implements Corrector {
	private final DiscreteProbabilityCollectionSampler<Corrector> correctorSampler;
	private final List<CompoundCorrectorStep> stepsList;

	public CompoundCorrector(CompoundCorrectorStep step, CompoundCorrectorStep... steps) {
		stepsList = ImmutableList.<CompoundCorrectorStep>builder().add(step).addAll(Arrays.asList(steps)).build();
		correctorSampler = new DiscreteProbabilityCollectionSampler<Corrector>(new JDKRandomWrapper(new Random()),
				stepsList.stream().collect(
						Collectors.toMap(CompoundCorrectorStep::getCorrector, CompoundCorrectorStep::getWeight)));
	}

	@Override
	public String description() {
		return "Compound corrector: " + Joiner.on(", ").join(stepsList.stream()
				.map(s -> "[" + s.getCorrector().description() + " weight " + s.getWeight() + "]").iterator());
	}

	@Override
	public List<MutationStep> correct(List<MutationStep> generationList) {
		// partition generation list by correctors
		Map<Corrector, List<MutationStep>> correctorsAndTargets = new HashMap<>();
		generationList.stream().sequential().forEach(step -> {
			addCorrectorTarget(correctorsAndTargets, correctorSampler.sample(), step);
		});
		// execute correctors on their partition
		correctorsAndTargets.entrySet().stream().forEach(entry -> entry.getKey().correct(entry.getValue()));
		// merge and return corrected lists.
		return correctorsAndTargets.values().stream().flatMap(Collection::stream).collect(Collectors.toList());
	}

	private void addCorrectorTarget(Map<Corrector, List<MutationStep>> correctorsAndTargets, Corrector corrector,
			MutationStep step) {
		List<MutationStep> partition;
		try {
			partition = correctorsAndTargets.get(corrector);
		} catch (NullPointerException ex) {
			// partition not found, set to null to create new
			partition = null;
		}
		if (partition == null) {
			// create new partition
			partition = new ArrayList<>();
			correctorsAndTargets.put(corrector, partition);
		}
		// add step to partition
		partition.add(step);
	}

}
