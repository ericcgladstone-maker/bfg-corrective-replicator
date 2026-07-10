package bfg.corrector;

import java.util.List;

import bfg.Describable;
import bfg.MutationStep;

public interface Corrector extends Describable {

	List<MutationStep> correct(List<MutationStep> generationList);

}
