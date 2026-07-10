package bfg.mutator;

import java.util.Arrays;
import java.util.concurrent.ThreadLocalRandom;

import bfg.Describable;
import bfg.MutationStep;
//Drop words from parent, at 5 %
//
//Mutate character at 15%: alphabet replacement, shift to lower case
//
//Insert space/letter into existing word
//
//Insert words from dictionary, between existing words at 5 %
//
//
//ford
//fork
//for k
//for k lace
//
//ford
//foty
import bfg.misc.StringSanitizer;

public class Mutator implements Describable {
	private final char[] mutatableInput;
	private final char[] mutatableOutput;
	private final double mutateCharProbability;
	private final double insertCharProbability;
	private final double insertSpaceProbability;
	private final double deleteCharProbability;
	private final double deleteSpaceProbability;
	private final StringSanitizer stringSanitizer;

	public Mutator(char[] mutatableInput, char[] mutatableOutput, double mutateCharProbability,
			double insertCharProbability, double deleteCharProbability, double insertSpaceProbability,
			double deleteSpaceProbability) {
		this.mutatableInput = Arrays.copyOf(mutatableInput, mutatableInput.length);
		this.mutatableOutput = Arrays.copyOf(mutatableOutput, mutatableOutput.length);
		this.mutateCharProbability = mutateCharProbability;
		this.insertCharProbability = insertCharProbability;
		this.deleteCharProbability = deleteCharProbability;
		this.insertSpaceProbability = insertSpaceProbability;
		this.deleteSpaceProbability = deleteSpaceProbability;
		this.stringSanitizer = StringSanitizer.getInstance();
		Arrays.sort(this.mutatableInput);
	}

	public Mutator(String validChars, double mutateCharProbability, double insertCharProbability,
			double deleteCharProbability, double insertSpaceProbability, double deleteSpaceProbability) {
		this(validChars, validChars, mutateCharProbability, insertCharProbability, deleteCharProbability,
				insertSpaceProbability, deleteSpaceProbability);
	}

	public Mutator(String mutatableInput, String mutatableOutput, double mutateCharProbability,
			double insertCharProbability, double deleteCharProbability, double insertSpaceProbability,
			double deleteSpaceProbability) {
		this(mutatableInput.toCharArray(), mutatableOutput.toCharArray(), mutateCharProbability, insertCharProbability,
				deleteCharProbability, insertSpaceProbability, deleteSpaceProbability);
	}

	private boolean doMutateChar() {
		return ThreadLocalRandom.current().nextDouble() < mutateCharProbability;
	}

	private boolean doInsertChar() {
		return ThreadLocalRandom.current().nextDouble() < insertCharProbability;
	}

	private boolean doDeleteChar() {
		return ThreadLocalRandom.current().nextDouble() < deleteCharProbability;
	}

	private boolean doInsertSpace() {
		return ThreadLocalRandom.current().nextDouble() < insertSpaceProbability;
	}

	private boolean doDeleteSpace() {
		return ThreadLocalRandom.current().nextDouble() < deleteSpaceProbability;
	}

	private char getReplacement() {
		int replaceWithNdx = ThreadLocalRandom.current().nextInt(mutatableOutput.length);
		char replaceWith = mutatableOutput[replaceWithNdx];
		return replaceWith;
	}

	private boolean isReplaceable(char ch) {
		return Arrays.binarySearch(mutatableInput, ch) >= 0;
	}

	private boolean isSpace(char inch) {
		return inch == ' ';
	}

	public MutationStep mutate(MutationStep step) {
		StringBuilder sb = new StringBuilder();
		for (char inch : step.getParentString().toCharArray()) {
			// check if replacing character
			if (isReplaceable(inch)) {
				if (!doDeleteChar()) {
					char outch;
					if (doMutateChar()) {
						outch = getReplacement();
					} else {
						outch = inch;
					}
					sb.append(Character.toLowerCase(outch));
				}
			} else if (isSpace(inch) && doDeleteSpace()) {
				// do nothing
			} else {
				sb.append(inch);
			}
			// check if inserting character
			if (doInsertChar()) {
				sb.append(getReplacement());
			}
			// check if inserting space
			if (doInsertSpace()) {
				sb.append(' ');
			}
		}
		step.setChildString(stringSanitizer.sanitize(sb.toString()));
		return step;
	}

	@Override
	public String description() {
		return "Mutator [mutatableInput=" + Arrays.toString(mutatableInput) + ", mutatableOutput="
				+ Arrays.toString(mutatableOutput) + ", mutateCharProbability=" + mutateCharProbability
				+ ", insertCharProbability=" + insertCharProbability + ", insertSpaceProbability="
				+ insertSpaceProbability + ", deleteCharProbability=" + deleteCharProbability
				+ ", deleteSpaceProbability=" + deleteSpaceProbability + "]";
	}

}
