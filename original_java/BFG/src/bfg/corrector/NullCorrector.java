package bfg.corrector;

import java.util.List;

import bfg.MutationStep;

public class NullCorrector implements Corrector {

	@Override
	public List<MutationStep> correct(List<MutationStep> generationList) {
		return generationList;
	}

	@Override
	public String description() {
		return "Null Corrector";
	}

}
