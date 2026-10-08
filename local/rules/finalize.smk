rule infer_major_lineage:
    input:
        metadata="data/metadata_validated.tsv",
    output:
        metadata="data/metadata_lineages.tsv",
    params:
        nextclade_field="genotype_nextclade",
    log:
        "logs/infer_major_lineage.txt",
    shell:
        """
        cat {input.metadata:q} \
        | csvtk -tl mutate \
          -f {params.nextclade_field} \
          -n genotype \
          -p "^([0-9][A-Z]+)" \
        | csvtk -tl mutate \
          -f {params.nextclade_field} \
          -n major_lineage \
          -p "^([0-9][A-Z]+(?:_[A-Z])?)" \
        | csvtk -tl mutate \
          -f {params.nextclade_field} \
          -n minor_lineage \
        > {output.metadata:q}
        """


rule split_outputs_by_serotype:
    input:
        metadata="data/metadata_linked.tsv",
        sequences="data/sequences_linked.fasta",
    output:
        metadata=expand("results/metadata_{serotype}.tsv", serotype=SEROTYPES),
        sequences=expand("results/sequences_{serotype}.fasta", serotype=SEROTYPES),
        include=expand("results/include_{serotype}.txt", serotype=SEROTYPES),
    params:
        serotypes=" ".join(SEROTYPES),
        columns=",".join(config["metadata_columns"]),
    log:
        "logs/split_outputs_by_serotype.txt",
    shell:
        r"""
        exec &> >(tee {log:q})

        python3 scripts/split-by-serotype.py \
            --metadata {input.metadata:q} \
            --sequences {input.sequences:q} \
            --id-column accession \
            --serotype-column serotype_genbank \
            --serotypes {params.serotypes} \
            --columns {params.columns:q} \
            --output-dir results \
            --write-include
        """
