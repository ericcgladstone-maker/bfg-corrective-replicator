package bfg.reaper;

import java.util.List;

import bfg.Describable;
import bfg.MutationStep;

public interface Reaper extends Describable {

	public List<MutationStep> reap(List<MutationStep> generationList);

}
